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
    
    New Flow:
    1. Analysis (Claude) → Determines strategy: Gemini vs ImageMagick vs Both
    2. Background Removal (remove.bg) → Clean background first
    3. Gemini Editing (if selected) → Advanced AI-powered editing  
    4. ImageMagick Optimization (if selected/fallback) → Traditional processing
    5. Quality Control (Claude) → Validates results with fallback decisions
    """
    
    writer = get_stream_writer()
    
    # Initialize or restore state
    image_path = inputs["image_path"]
    custom_instructions = inputs.get("custom_instructions")
    retry_count = (previous or {}).get("retry_count", 0)
    
    writer({
        "workflow": "enhanced_started",
        "image_path": image_path,
        "retry_count": retry_count,
        "message": f"Starting enhanced 5-agent processing for {Path(image_path).name}"
    })
    
    try:
        # 🔍 Stage 1: Enhanced Analysis
        writer({
            "stage": "analysis",
            "message": "Analyzing image and determining optimal editing strategy"
        })
        analysis = await run_enhanced_analysis_agent(image_path, custom_instructions)
        editing_strategy = analysis.get("editing_strategy", "imagemagick")
        
        writer({
            "stage": "analysis_complete",
            "strategy": editing_strategy,
            "message": f"Analysis complete - Strategy: {editing_strategy}"
        })
        
        # Track intermediate files for cleanup
        intermediate_files = []
        
        # Skip background removal initially - do it after Gemini editing
        current_image = image_path
        
        # 🎨 Stage 3: Gemini Editing (if strategy includes it)
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
        
        # ⚡ Stage 4: ImageMagick Optimization (only if Gemini wasn't used)
        imagemagick_optimized_path = None
        if editing_strategy == "imagemagick":
            writer({
                "stage": "imagemagick_optimization", 
                "message": "Applying ImageMagick optimizations"
            })
            imagemagick_optimized_path = await run_imagemagick_agent(current_image, analysis)
            current_image = imagemagick_optimized_path
        elif editing_strategy == "both":
            writer({
                "stage": "imagemagick_skipped", 
                "message": "Skipping ImageMagick - Gemini already handled complex processing"
            })
        
        # 🖼️ Stage 4.5: Background Removal (after Gemini editing)
        if analysis.get("remove_background", False):
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
        
        # Skip ImageMagick fallback if Gemini was specifically chosen and used
        if (qc_result.get("needs_imagemagick_fallback", False) and 
            not imagemagick_optimized_path and 
            editing_strategy != "gemini"):
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
        if retry_count < 2:  # Max 2 retries
            writer({
                "workflow": "enhanced_retry",
                "attempt": retry_count + 1,
                "quality": final_quality,
                "issues": qc_result.get("issues_found", []),
                "message": f"🔄 Quality insufficient ({final_quality}/10), retrying with refined approach"
            })
            
            # Create refined analysis for retry
            refined_analysis = analysis.copy()
            
            # Adjust strategy based on QC feedback
            if editing_strategy == "gemini" and final_quality < 7:
                refined_analysis["editing_strategy"] = "imagemagick"
                refined_analysis["imagemagick_command"] = qc_result.get("imagemagick_suggestions", "-enhance")
            elif editing_strategy == "imagemagick" and final_quality < 7:
                refined_analysis["editing_strategy"] = "both"  # Try Gemini + ImageMagick
            
            # Recursive retry with refined approach
            return entrypoint.final(
                value=await enhanced_agentic_processor(
                    {
                        "image_path": image_path,
                        "custom_instructions": custom_instructions,
                        "refined_analysis": refined_analysis
                    }
                ),
                save={"retry_count": retry_count + 1}
            )
        
        # 😞 Final attempt - return best result even if not perfect
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
    
    # Check if enhanced_agentic_processor is a Pregel graph or function
    if hasattr(enhanced_agentic_processor, 'ainvoke'):
        # It's a Pregel graph, use ainvoke
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        result = await enhanced_agentic_processor.ainvoke({
            "image_path": image_path,
            "custom_instructions": custom_instructions
        }, config=config)
    else:
        # It's a function, call directly
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
    pattern: str = "*.{jpg,jpeg,png,webp}"
) -> Dict[str, Any]:
    """Process multiple images with the enhanced workflow"""
    
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
    
    # Process images with concurrency control
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