"""
Enhanced Agentic Photo Editor - 5-Agent Workflow with Gemini 2.5 Flash Image
Intelligent hybrid approach: Claude analysis → Gemini editing → ImageMagick fallback → QC
"""

from typing import TypedDict, Annotated, Dict, Any, Optional
from pathlib import Path
import operator
import asyncio
import os

from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer

from .agents_enhanced import (
    enhanced_analysis_agent,
    gemini_edit_agent,
    imagemagick_optimization_agent, 
    background_removal_agent,
    enhanced_qc_agent,
    AgentError
)

# Import lens correction module
try:
    from .lens_corrections_advanced import apply_lens_corrections
    LENS_CORRECTIONS_AVAILABLE = True
except ImportError:
    LENS_CORRECTIONS_AVAILABLE = False

# Try to import Wand-based agents
try:
    from .wand_optimization_agent import wand_optimization_agent, smart_crop_agent
    WAND_AVAILABLE = True
except ImportError:
    WAND_AVAILABLE = False
    wand_optimization_agent = imagemagick_optimization_agent  # Fallback
    smart_crop_agent = None


def finalize_output_with_quality_and_cleanup(
    current_path: str, 
    quality_score: float, 
    intermediate_files: list,
    passed_qc: bool
) -> str:
    """
    Rename final output based on quality and clean up intermediate files
    """
    final_path = current_path
    
    # Add quality indicator for poor results (≤8)
    if not passed_qc or quality_score <= 8:
        path_obj = Path(current_path)
        quality_suffix = f"-q{int(quality_score)}" if quality_score > 0 else "-qfail"
        new_name = f"{path_obj.stem}{quality_suffix}{path_obj.suffix}"
        final_path = str(path_obj.parent / new_name)
        
        # Rename the file
        try:
            import shutil
            shutil.move(current_path, final_path)
            print(f"📝 Renamed to indicate quality: {Path(final_path).name}")
        except Exception as e:
            print(f"⚠️ Failed to rename for quality indicator: {e}")
            final_path = current_path
    
    # Clean up intermediate files
    cleanup_count = 0
    for intermediate_file in intermediate_files:
        if intermediate_file and os.path.exists(intermediate_file) and intermediate_file != final_path:
            try:
                os.remove(intermediate_file)
                cleanup_count += 1
                print(f"🧹 Cleaned up: {Path(intermediate_file).name}")
            except Exception as e:
                print(f"⚠️ Failed to cleanup {Path(intermediate_file).name}: {e}")
    
    if cleanup_count > 0:
        print(f"🧹 Cleaned up {cleanup_count} intermediate files")
    
    return final_path


class EnhancedPhotoProcessingState(TypedDict):
    """State for the enhanced 5-agent workflow"""
    input_image_path: str
    analysis_report: Dict[str, Any]
    background_removed_path: str
    gemini_edited_path: str
    imagemagick_optimized_path: str
    final_image_path: str
    qc_report: Dict[str, Any]
    editing_strategy: str  # "gemini", "imagemagick", or "both"
    retry_count: int
    processing_logs: Annotated[list, operator.add]
    error_messages: Annotated[list, operator.add]


# Initialize checkpointer for state persistence
enhanced_checkpointer = InMemorySaver()


@task
async def run_enhanced_analysis_agent(image_path: str, custom_instructions: Optional[str] = None) -> Dict[str, Any]:
    """🔍 Enhanced analysis task wrapper"""
    try:
        return await enhanced_analysis_agent(image_path, custom_instructions)
    except AgentError as e:
        raise


@task
async def run_gemini_edit_agent(image_path: str, analysis: Dict[str, Any]) -> str:
    """🎨 Gemini editing task wrapper"""
    try:
        return await gemini_edit_agent(image_path, analysis)
    except AgentError as e:
        raise


@task
async def run_imagemagick_agent(image_path: str, analysis: Dict[str, Any]) -> str:
    """⚡ ImageMagick task wrapper"""
    try:
        return await imagemagick_optimization_agent(image_path, analysis)
    except AgentError as e:
        raise


@task
async def run_background_agent(image_path: str, analysis: Dict[str, Any]) -> str:
    """🖼️ Background removal task wrapper"""
    try:
        return await background_removal_agent(image_path, analysis)
    except AgentError as e:
        # Background removal is optional, return original path on failure
        return image_path


@task
async def run_lens_correction_agent(image_path: str, analysis: Dict[str, Any]) -> str:
    """Run lens correction agent if needed"""
    try:
        # Check if lens correction is needed
        needs_lens_correction = analysis.get("needs_lens_correction", False)
        lens_issues = analysis.get("lens_issues", [])
        
        if needs_lens_correction and lens_issues and LENS_CORRECTIONS_AVAILABLE:
            from .lens_corrections_advanced import apply_lens_corrections
            
            # Create output path for lens corrected image
            input_path = Path(image_path)
            output_path = input_path.parent / f"{input_path.stem}-lens-corrected{input_path.suffix}"
            
            # Apply lens corrections
            result = apply_lens_corrections(str(input_path), str(output_path))
            
            if result.get("corrections_applied", False):
                # Update analysis to indicate lens corrections were applied
                analysis["lens_corrections_applied"] = True
                return str(output_path)
        
        # Return original image path if no corrections applied
        analysis["lens_corrections_applied"] = False
        return image_path
    except AgentError as e:
        raise


@task
async def run_enhanced_qc_agent(image_path: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """✅ Enhanced QC task wrapper"""
    try:
        return await enhanced_qc_agent(image_path, analysis)
    except AgentError as e:
        raise


@entrypoint(checkpointer=enhanced_checkpointer)
async def enhanced_agentic_processor(
    inputs: Dict[str, Any],
    *,
    previous: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    🤖 Enhanced 5-Agent Photo Processing Workflow
    
    New Workflow Stages:
1. 📊 Analysis Agent (Claude Sonnet 4) - Determines optimal editing strategy
2. 🔍 Lens Correction Agent - Applies lens corrections using lensfunpy or ImageMagick fallback
3. 🧠 Background Removal Agent - Applies background removal using advanced segmentation
4. 🎨 Gemini Edit Agent - Uses Gemini 2.5 Flash Image for complex AI-powered editing
5. 🛠️ ImageMagick Agent - Traditional image processing for simple optimizations
6. ✅ QC Agent - Quality control and final evaluation
    """
    
    writer = get_stream_writer()
    
    # Initialize or restore state
    image_path = inputs["image_path"]
    custom_instructions = inputs.get("custom_instructions")
    # Get retry_count from inputs first (for recursive calls), then from previous state
    retry_count = inputs.get("retry_count", (previous or {}).get("retry_count", 0))
    
    writer({
        "workflow": "enhanced_started",
        "image_path": image_path,
        "retry_count": retry_count,
        "message": f"Starting enhanced 5-agent processing for {Path(image_path).name}"
    })
    
    try:
        # Check if ImageMagick is disabled by user
        skip_imagemagick = os.getenv("SKIP_IMAGEMAGICK", "false").lower() == "true"
        
        # 🔍 Stage 1: Enhanced Analysis
        writer({
            "stage": "analysis",
            "message": "Analyzing image and determining optimal editing strategy"
        })
        analysis = await run_enhanced_analysis_agent(image_path, custom_instructions)
        editing_strategy = analysis.get("editing_strategy", "imagemagick")
        
        # Override strategy if ImageMagick is disabled
        if skip_imagemagick and editing_strategy == "imagemagick":
            editing_strategy = "gemini"  # Fall back to Gemini if available
            writer({
                "stage": "strategy_override",
                "message": "ImageMagick disabled, using Gemini instead"
            })
        
        writer({
            "stage": "analysis_complete",
            "strategy": editing_strategy,
            "message": f"Analysis complete - Strategy: {editing_strategy}"
        })
        
        # Track intermediate files for cleanup
        intermediate_files = []
        
        # Initialize current_image to track the working image path
        current_image = image_path
        
        # ✂️ Stage 2: Smart Cropping (if needed)
        if smart_crop_agent and analysis.get("needs_cropping", False):
            writer({
                "stage": "smart_cropping",
                "message": "Analyzing and applying smart crop"
            })
            try:
                cropped_path, crop_info = await smart_crop_agent(current_image, analysis)
                if crop_info.get("cropped", False):
                    current_image = cropped_path
                    intermediate_files.append(cropped_path)
                    writer({
                        "stage": "crop_complete",
                        "message": f"Cropped image: {crop_info.get('reduction', 'N/A')} reduction"
                    })
            except Exception as e:
                writer({
                    "stage": "crop_skipped",
                    "message": f"Cropping failed, continuing: {str(e)}"
                })
        
        # 🔍 Stage 3: Defect Detection and Repair (NEW)
        # Check if repair is enabled and not already processed
        skip_repair = os.getenv("SKIP_REPAIR", "false").lower() == "true"
        
        if skip_repair:
            writer({
                "stage": "defect_repair_skipped",
                "message": "🔧 Defect repair disabled by user"
            })
            print("🔧 Defect repair disabled by user preference")
        elif "repaired" in current_image or "inpainted" in current_image:
            writer({
                "stage": "defect_repair_skipped",
                "message": "🔧 Defect repair already applied"
            })
            print("🔧 Defect repair already applied to image")
        else:
            writer({
                "stage": "defect_detection",
                "message": "🔧 Starting defect detection and repair"
            })
            print("🔧 Starting defect detection and repair process...")
            
            try:
                # Import repair agents
                from .defect_detection_agent import detect_defects_agent
                from .opencv_inpaint_agent import opencv_inpaint_agent, smart_inpaint
                from .gmic_repair_agent import gmic_repair_agent, check_gmic_available
                
                # Detect defects - get sensitivity from environment or analysis
                sensitivity = int(os.getenv("DEFECT_SENSITIVITY", "50"))
                print(f"   🔍 Analyzing image for defects (sensitivity: {sensitivity})")
                defect_result = await detect_defects_agent(
                    current_image,
                    sensitivity=sensitivity
                )
                
                if defect_result.get("has_defects"):
                    defect_count = defect_result.get("defect_count", 0)
                    print(f"   ⚠️ Found {defect_count} defect pixels")
                    writer({
                        "stage": "defect_repair",
                        "message": f"Found defects: {', '.join(defect_result.get('defect_types', []))}"
                    })
                    
                    # Try G'MIC first if available
                    repair_applied = False
                    if check_gmic_available():
                        print("   🔧 Attempting G'MIC repair...")
                        repair_result = await gmic_repair_agent(
                            current_image,
                            mask_path=defect_result.get("mask_path"),
                            repair_mode="auto"
                        )
                        if repair_result.get("success"):
                            current_image = repair_result["output_path"]
                            intermediate_files.append(repair_result["output_path"])
                            repair_applied = True
                            writer({
                                "stage": "repair_complete",
                                "message": f"G'MIC repair applied: {', '.join(repair_result.get('filters_applied', []))}"
                            })
                            print(f"   ✅ G'MIC repair successful: {', '.join(repair_result.get('filters_applied', []))}")
                    else:
                        print("   ℹ️ G'MIC not available")
                    
                    # Fall back to OpenCV if G'MIC didn't work or wasn't available
                    if not repair_applied and defect_result.get("mask_path"):
                        print("   🎨 Attempting OpenCV inpainting...")
                        # Use aggressive mode if sensitivity is high
                        aggressive = sensitivity > 60
                        inpaint_result = await smart_inpaint(
                            current_image,
                            defect_result,
                            aggressive=aggressive
                        )
                        if inpaint_result.get("success"):
                            current_image = inpaint_result["output_path"]
                            intermediate_files.append(inpaint_result["output_path"])
                            repair_applied = True
                            writer({
                                "stage": "repair_complete",
                                "message": f"OpenCV inpainting applied: {inpaint_result.get('method_used', 'auto')}"
                            })
                            print(f"   ✅ OpenCV repair successful: {inpaint_result.get('method_used', 'auto')} method")
                        else:
                            print(f"   ⚠️ OpenCV repair failed: {inpaint_result.get('message', 'Unknown error')}")
                    
                    if not repair_applied:
                        print("   ⚠️ No repair methods succeeded, continuing with original image")
                else:
                    writer({
                        "stage": "defect_detection_complete",
                        "message": "No significant defects detected"
                    })
                    print("   ✅ No significant defects detected, skipping repair")
                    
            except Exception as e:
                writer({
                    "stage": "repair_skipped",
                    "message": f"Defect repair failed: {str(e)}"
                })
                print(f"   ❌ Defect repair error: {str(e)}")
        
        # Log repair summary
        if not skip_repair:
            if current_image != image_path:
                print(f"   ✅ DEFECT REPAIR COMPLETED - Image was repaired")
            else:
                print(f"   ℹ️ DEFECT REPAIR COMPLETED - No repairs applied")
        
        # 🔍 Stage 4: Lens Correction (if needed)
        # Check if lens corrections were already applied in Streamlit or disabled by user
        already_corrected = "lens-corrected" in image_path or "corrected_" in image_path
        skip_lens_correction = os.getenv("SKIP_LENS_CORRECTION", "false").lower() == "true"
        
        lens_corrected_path = None
        needs_lens_correction = analysis.get("needs_lens_correction", False)
        lens_issues = analysis.get("lens_issues", [])
        
        if not already_corrected and not skip_lens_correction and needs_lens_correction and lens_issues:
            writer({
                "stage": "lens_correction",
                "message": "Applying lens corrections"
            })
            lens_corrected_path = await run_lens_correction_agent(current_image, analysis)
            if lens_corrected_path != current_image:
                current_image = lens_corrected_path
                intermediate_files.append(lens_corrected_path)
        elif already_corrected:
            writer({
                "stage": "lens_correction_skipped",
                "message": "Lens corrections already applied"
            })
        elif skip_lens_correction:
            writer({
                "stage": "lens_correction_skipped",
                "message": "Lens corrections disabled by user"
            })
        
        # Skip background removal initially - do it after Gemini editing
        # This ensures lens correction is applied to the original image first
        gemini_edited_path = None
        
        # 🎨 Stage 4: Gemini Editing (if strategy includes it)
        gemini_edited_path = None
        if editing_strategy in ["gemini", "both"]:
            writer({
                "stage": "gemini_editing",
                "message": "Applying advanced AI editing with Gemini 2.5 Flash Image"
            })
            try:
                gemini_edited_path = await run_gemini_edit_agent(current_image, analysis)
                current_image = gemini_edited_path
                
                writer({
                    "stage": "gemini_complete",
                    "message": "Gemini editing completed successfully"
                })
            except AgentError as e:
                writer({
                    "stage": "gemini_failed",
                    "message": f"Gemini editing failed: {e}, falling back to ImageMagick"
                })
                # Force ImageMagick fallback
                editing_strategy = "imagemagick"
        
        # ⚡ Stage 5: ImageMagick Optimization (only if Gemini wasn't used and not skipped by user)
        imagemagick_optimized_path = None
        
        if skip_imagemagick:
            writer({
                "stage": "imagemagick_skipped",
                "message": "ImageMagick optimization disabled by user"
            })
        elif editing_strategy == "imagemagick":
            writer({
                "stage": "imagemagick_optimization", 
                "message": "Applying ImageMagick optimizations" + (" via Wand" if WAND_AVAILABLE else "")
            })
            # Use Wand agent if available, otherwise fall back to subprocess
            if WAND_AVAILABLE:
                imagemagick_optimized_path = await wand_optimization_agent(current_image, analysis)
            else:
                imagemagick_optimized_path = await run_imagemagick_agent(current_image, analysis)
            current_image = imagemagick_optimized_path
        elif editing_strategy == "both":
            writer({
                "stage": "imagemagick_skipped", 
                "message": "Skipping ImageMagick - Gemini already handled complex processing"
            })
        
        # 🖼️ Stage 4.5: Background Removal (after Gemini editing)
        # Check if background removal is enabled by user (not just analysis suggestion)
        skip_background_removal = os.getenv("SKIP_BACKGROUND_REMOVAL", "false").lower() == "true"
        if not skip_background_removal and analysis.get("remove_background", False):
            writer({
                "stage": "background_removal_final",
                "message": "Removing background from enhanced image"
            })
            bg_removed_final = await run_background_agent(current_image, analysis)
            if bg_removed_final != current_image:
                # Track the intermediate PNG and WebP files created by background removal
                png_file = str(Path(current_image).parent / f"{Path(current_image).stem}-no-bg.png")
                webp_file = str(Path(current_image).parent / f"{Path(current_image).stem}-no-bg.webp")
                if os.path.exists(png_file):
                    intermediate_files.append(png_file)
                if os.path.exists(webp_file) and webp_file != bg_removed_final:
                    intermediate_files.append(webp_file)
            current_image = bg_removed_final
        
        # ✅ Stage 5: Enhanced Quality Control
        writer({
            "stage": "quality_control",
            "message": "Performing enhanced quality control check"
        })
        qc_result = await run_enhanced_qc_agent(current_image, analysis)
        
        # 🔄 Stage 6: ImageMagick Fallback Decision
        final_image_path = current_image
        
        # Skip ImageMagick fallback if Gemini was specifically chosen and used or if ImageMagick is disabled
        if (qc_result.get("needs_imagemagick_fallback", False) and 
            not imagemagick_optimized_path and 
            editing_strategy != "gemini" and
            not skip_imagemagick):
            writer({
                "stage": "imagemagick_fallback",
                "message": "QC recommends ImageMagick fallback - applying additional optimization"
            })
            
            # Apply ImageMagick suggestions from QC
            fallback_analysis = analysis.copy()
            fallback_analysis["imagemagick_command"] = qc_result.get("imagemagick_suggestions", "-enhance")
            
            try:
                fallback_optimized = await run_imagemagick_agent(current_image, fallback_analysis)
                
                # Re-run QC on fallback result
                fallback_qc = await run_enhanced_qc_agent(fallback_optimized, analysis)
                
                # Use fallback result if it's better
                if fallback_qc.get("quality_score", 0) > qc_result.get("quality_score", 0):
                    final_image_path = fallback_optimized
                    qc_result = fallback_qc
                    writer({
                        "stage": "fallback_success",
                        "message": f"ImageMagick fallback improved quality: {fallback_qc.get('quality_score', 0)}/10"
                    })
                
            except AgentError as e:
                writer({
                    "stage": "fallback_failed",
                    "message": f"ImageMagick fallback failed: {e}"
                })
        
        # 🎯 Final Results
        final_quality = qc_result.get("quality_score", 0)
        passed_qc = qc_result.get("passed", False)
        
        if passed_qc and final_quality >= 9:
            # 🎯 Optional Targeted Enhancement Stage (after successful ImageMagick)
            use_targeted_enhancement = os.getenv("USE_TARGETED_ENHANCEMENT", "false").lower() == "true"
            
            if use_targeted_enhancement and editing_strategy in ["imagemagick", "both"]:
                writer({
                    "workflow": "targeted_enhancement_start",
                    "message": "🎯 Starting targeted Gemini enhancement on specific areas..."
                })
                
                try:
                    from src.targeted_enhancement import targeted_enhancement_pipeline
                    
                    targeted_result = await targeted_enhancement_pipeline(
                        final_image_path,
                        custom_instructions=custom_instructions,
                        max_areas=3,
                        initial_analysis=analysis
                    )
                    
                    if targeted_result.get("enhanced") and targeted_result.get("final_image"):
                        final_image_path = targeted_result["final_image"]
                        writer({
                            "workflow": "targeted_enhancement_success",
                            "areas_enhanced": targeted_result.get("areas_enhanced", 0),
                            "message": f"✅ Enhanced {targeted_result.get('areas_enhanced', 0)} targeted areas"
                        })
                except Exception as e:
                    writer({
                        "workflow": "targeted_enhancement_error",
                        "error": str(e),
                        "message": f"⚠️ Targeted enhancement failed: {e}, using standard result"
                    })
            
            # Finalize with quality indicators and cleanup
            final_image_path = finalize_output_with_quality_and_cleanup(
                final_image_path, final_quality, intermediate_files, passed_qc
            )
            
            writer({
                "workflow": "enhanced_success",
                "final_image": final_image_path,
                "quality_score": final_quality,
                "strategy_used": editing_strategy,
                "message": f"✅ Enhanced processing complete - Quality: {final_quality}/10"
            })
            
            return entrypoint.final(
                value={
                    "final_image": final_image_path,
                    "qc_passed": True,
                    "quality_score": final_quality,
                    "editing_strategy": editing_strategy,
                    "gemini_used": gemini_edited_path is not None,
                    "imagemagick_used": imagemagick_optimized_path is not None,
                    "targeted_enhancement_used": use_targeted_enhancement,
                    "retry_count": retry_count
                },
                save={
                    "analysis": analysis,
                    "final_path": final_image_path,
                    "qc_report": qc_result,
                    "strategy": editing_strategy,
                    "retry_count": retry_count,
                    "processing_complete": True
                }
            )
        
        # 🔄 Retry Logic (if quality is still poor)
        MAX_RETRIES = 2
        if retry_count < MAX_RETRIES and final_quality < 7:  # Max 2 retries, only if quality is poor
            writer({
                "workflow": "enhanced_retry",
                "attempt": retry_count + 1,
                "max_attempts": MAX_RETRIES,
                "quality": final_quality,
                "issues": qc_result.get("issues_found", []),
                "message": f"🔄 Quality insufficient ({final_quality}/10), retry {retry_count + 1}/{MAX_RETRIES}"
            })
            
            # Create refined analysis for retry
            refined_analysis = analysis.copy()
            
            # Adjust strategy based on QC feedback
            if editing_strategy == "gemini" and final_quality < 7:
                refined_analysis["editing_strategy"] = "imagemagick"
                refined_analysis["imagemagick_command"] = qc_result.get("imagemagick_suggestions", "-enhance")
            elif editing_strategy == "imagemagick" and final_quality < 7:
                refined_analysis["editing_strategy"] = "both"  # Try Gemini + ImageMagick
            
            # Recursive retry with refined approach - pass retry count forward
            import uuid
            config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            retry_result = await enhanced_agentic_processor.ainvoke(
                {
                    "image_path": image_path,
                    "custom_instructions": custom_instructions,
                    "refined_analysis": refined_analysis,
                    "retry_count": retry_count + 1  # Pass the incremented count
                },
                config=config
            )
            return entrypoint.final(
                value=retry_result,
                save={"retry_count": retry_count + 1}
            )
        
        # 😞 Final attempt - return best result even if not perfect
        writer({
            "workflow": "retry_limit_reached",
            "retry_count": retry_count,
            "final_quality": final_quality,
            "message": f"⚠️ Retry limit reached ({retry_count} attempts), accepting result with quality {final_quality}/10"
        })
        
        # Finalize with quality indicators and cleanup
        final_image_path = finalize_output_with_quality_and_cleanup(
            final_image_path, final_quality, intermediate_files, passed_qc
        )
        
        writer({
            "workflow": "enhanced_complete_imperfect",
            "final_image": final_image_path,
            "quality_score": final_quality,
            "message": f"⚠️ Processing complete with quality score: {final_quality}/10 (max retries reached)"
        })
        
        return entrypoint.final(
            value={
                "final_image": final_image_path,
                "qc_passed": False,
                "quality_score": final_quality,
                "editing_strategy": editing_strategy,
                "retry_count": retry_count,
                "warning": "Quality below threshold despite retries"
            },
            save={
                "analysis": analysis,
                "final_path": final_image_path,
                "qc_report": qc_result,
                "strategy": editing_strategy,
                "retry_count": retry_count,
                "processing_complete": True
            }
        )
        
    except Exception as e:
        error_msg = f"Enhanced workflow failed: {str(e)}"
        writer({
            "workflow": "enhanced_error",
            "error": error_msg,
            "message": f"❌ {error_msg}"
        })
        
        return entrypoint.final(
            value={
                "error": error_msg,
                "final_image": None,
                "qc_passed": False,
                "quality_score": 0
            },
            save={
                "error": error_msg,
                "retry_count": retry_count,
                "processing_failed": True
            }
        )


# Convenience functions for batch processing
async def process_single_image_enhanced(
    image_path: str,
    custom_instructions: Optional[str] = None,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Process a single image with the enhanced workflow"""
    
    # Set up custom instructions in environment if provided
    if custom_instructions:
        os.environ["CUSTOM_PROCESSING_INSTRUCTIONS"] = custom_instructions
    
    # Process with enhanced workflow
    import uuid
    
    # Check if enhanced_agentic_processor is a Pregel graph or callable function
    if hasattr(enhanced_agentic_processor, 'ainvoke'):
        # It's a Pregel graph, use ainvoke
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        result = await enhanced_agentic_processor.ainvoke({
            "image_path": image_path,
            "custom_instructions": custom_instructions
        }, config=config)
    else:
        # It's a regular function (shouldn't happen with @entrypoint, but just in case)
        result = await enhanced_agentic_processor({
            "image_path": image_path,
            "custom_instructions": custom_instructions
        })
    
    # Move output if different directory specified
    if output_dir and result.get("final_image"):
        output_path = Path(output_dir) / Path(result["final_image"]).name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move processed file
        import shutil
        if Path(result["final_image"]).exists():
            shutil.move(result["final_image"], str(output_path))
            result["final_image"] = str(output_path)
        else:
            print(f"⚠️ Warning: Final image not found at {result['final_image']}")
            # Check if file exists in temp directory and copy it
            temp_files = list(Path("/tmp/agentic-photo-editor-temp").glob("*.webp"))
            if temp_files:
                latest_file = max(temp_files, key=lambda p: p.stat().st_mtime)
                print(f"📁 Found recent file in temp directory: {latest_file}")
                shutil.copy2(latest_file, str(output_path))
                result["final_image"] = str(output_path)
    
    return result


async def process_image_batch_enhanced(
    input_dir: str,
    output_dir: Optional[str] = None,
    max_concurrent: int = 3,
    custom_instructions: Optional[str] = None,
    pattern: str = "*.{jpg,jpeg,png,webp}",
    use_batch_consistency: bool = True
) -> Dict[str, Any]:
    """Process multiple images with the enhanced workflow and optional batch consistency"""
    
    input_path = Path(input_dir)
    if not input_path.exists():
        raise ValueError(f"Input directory not found: {input_dir}")
    
    # Find all matching images
    image_files = []
    for ext in ['jpg', 'jpeg', 'png', 'webp']:
        image_files.extend(list(input_path.glob(f"*.{ext}")))
        image_files.extend(list(input_path.glob(f"*.{ext.upper()}")))
    
    if not image_files:
        raise ValueError(f"No supported images found in: {input_dir}")
    
    # Use batch consistency if enabled and multiple images
    if use_batch_consistency and len(image_files) > 1:
        from .batch_consistency import process_batch_with_consistency
        print(f"🎯 Using batch consistency mode for {len(image_files)} images")
        return await process_batch_with_consistency(
            [str(img) for img in image_files],
            custom_instructions,
            output_dir,
            max_concurrent
        )
    
    # Process images with concurrency control (original method)
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_single(image_path):
        async with semaphore:
            return await process_single_image_enhanced(
                str(image_path), 
                custom_instructions,
                output_dir
            )
    
    # Execute batch processing
    tasks = [process_single(img) for img in image_files]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Compile batch results
    successful = sum(1 for r in results if isinstance(r, dict) and r.get("qc_passed", False))
    failed = len(results) - successful
    
    return {
        "total_images": len(image_files),
        "successful": successful,
        "failed": failed,
        "results": results,
        "success_rate": successful / len(image_files) if image_files else 0
    }