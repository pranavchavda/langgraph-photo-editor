"""
Enhanced Agentic Photo Editor - 5-Agent System with Gemini 2.5 Flash Image
Combines Claude Sonnet 4 analysis with Gemini 2.5 Flash Image editing and ImageMagick optimization
"""

import asyncio
import os
import base64
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List

import google.generativeai as genai
from anthropic import AsyncAnthropic
import requests
from langgraph.config import get_stream_writer
from langgraph.func import task

# Global clients - initialized lazily
anthropic_client = None

def get_anthropic_client():
    """Get or create Anthropic client with current API key"""
    global anthropic_client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise AgentError("ANTHROPIC_API_KEY not set")
    if anthropic_client is None or anthropic_client.api_key != api_key:
        anthropic_client = AsyncAnthropic(api_key=api_key)
    return anthropic_client

def configure_gemini():
    """Configure Gemini with current API key"""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
    else:
        raise AgentError("GEMINI_API_KEY not set")


class AgentError(Exception):
    """Custom exception for agent failures"""
    pass


def get_imagemagick_command():
    """Get the correct ImageMagick command for the platform"""
    import shutil
    
    # Try different ImageMagick command variations
    for cmd in ['magick', 'convert', 'imagemagick']:
        if shutil.which(cmd):
            return cmd
    
    # If no command found, return None
    return None


def encode_image_to_base64(image_path: str) -> str:
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def get_image_media_type(image_path: str) -> str:
    """Get media type for image based on actual file content, not just extension"""
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            format_map = {
                'JPEG': 'image/jpeg',
                'PNG': 'image/png',
                'WEBP': 'image/webp'
            }
            return format_map.get(img.format, 'image/jpeg')
    except Exception:
        # Fallback to extension-based detection
        ext = Path(image_path).suffix.lower()
        media_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg', 
            '.png': 'image/png',
            '.webp': 'image/webp'
        }
        return media_types.get(ext, 'image/jpeg')


async def enhanced_analysis_agent(image_path: str, custom_instructions: Optional[str] = None) -> Dict[str, Any]:
    """
    🔍 Enhanced Analysis Agent - Claude Sonnet 4 analyzes image and decides editing strategy
    
    Now determines whether to use Gemini 2.5 Flash Image editing or ImageMagick optimization
    """
    writer = get_stream_writer()
    
    writer({
        "agent": "analysis", 
        "status": "analyzing",
        "message": f"Analyzing {Path(image_path).name} and determining optimal editing strategy"
    })
    
    # Encode image
    image_base64 = encode_image_to_base64(image_path)
    media_type = get_image_media_type(image_path)
    
    # Enhanced analysis prompt for hybrid workflow
    analysis_prompt = """
    Analyze this product image and determine the optimal editing strategy. You must decide between:
    1. **Gemini 2.5 Flash Image** - Advanced AI editing for complex tasks
    2. **ImageMagick** - Traditional optimization for simple adjustments
    
    Evaluate the image for:
    - **Lens Distortion**: Barrel distortion, pincushion distortion, vignetting, chromatic aberration
    - **Surface Materials**: Chrome, stainless steel, matte surfaces, glass, plastic
    - **Lighting Issues**: Harsh shadows, overexposure, uneven lighting, color casts
    - **Dust and Sensor Debris**: Visible dust spots, sensor debris, dirt on surfaces
    - **Complex Problems**: Artifacts, unwanted objects, background issues
    - **Color Quality**: Saturation, vibrancy, accuracy needs
    
    **GEMINI EDITING** is best for:
    - Complex lighting corrections and color casts
    - Selective object editing (enhance chrome without affecting other areas)
    - Background modifications and artifact removal
    - Dust and sensor debris removal
    - Advanced color correction
    
    **IMAGEMAGICK** is sufficient for:
    - Simple brightness/contrast adjustments
    - Basic color saturation changes
    - Sharpening and noise reduction
    - Straightforward optimizations
    
    **LENS CORRECTION POLICY**:
    - Lens corrections (barrel/pincushion distortion, vignetting, chromatic aberration) are handled separately by the lensfun library.
    - Do NOT include lens correction steps in gemini_instructions.
    - ImageMagick lens corrections are fallback options only, to be used when lensfunpy is not available.
    - You may still report lens_issues and needs_lens_correction for downstream processing by lensfun.
    
    **BACKGROUND REMOVAL POLICY**:
    - Background removal is ENABLED by default for all product photography
    - Only set remove_background: false if user explicitly requests "no background removal", "keep background", or "no bg removal"
    - For e-commerce and product photos, transparent backgrounds are preferred
    
    Return analysis as JSON with:
    - lens_issues: [detected lens distortions: barrel, pincushion, vignetting, chromatic_aberration]
    - needs_lens_correction: boolean (true if lens issues detected)
    - lens_corrections_applied: boolean (true if lens corrections will be applied by dedicated lens correction step)
    - dust_issues: [detected dust problems: spots, sensor_debris, surface_dirt]
    - needs_dust_removal: boolean (true if dust issues detected)
    - surface_materials: [materials detected]
    - lighting_issues: [specific problems]
    - color_problems: [color issues]
    - complex_problems: [issues requiring AI editing]
    - editing_strategy: "gemini" or "imagemagick" or "both"
    - gemini_instructions: string (detailed instructions for Gemini editing, exclude lens corrections)
    - imagemagick_command: string (ImageMagick parameters, if needed)
    - editing_explanation: string (why this strategy was chosen)
    - remove_background: boolean (default: true, unless user explicitly says no)
    - optimization_priority: [ordered list of what to focus on]
    """
    
    # Add custom instructions
    if custom_instructions:
        analysis_prompt += f"""
        
    **CUSTOM USER INSTRUCTIONS**: {custom_instructions}
    
    Incorporate these user preferences into your editing strategy:
    - If user wants specific styles, use Gemini for complex styling
    - If user wants simple adjustments, ImageMagick may be sufficient
    - Always prioritize user intent in your strategy choice
    """
    
    try:
        client = get_anthropic_client()
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1200,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64
                        }
                    },
                    {"type": "text", "text": analysis_prompt}
                ]
            }]
        )
        
        # Parse response
        analysis_text = response.content[0].text
        
        try:
            # Extract JSON from response
            if "```json" in analysis_text:
                json_start = analysis_text.find("```json") + 7
                json_end = analysis_text.find("```", json_start)
                json_text = analysis_text[json_start:json_end].strip()
            elif "{" in analysis_text:
                json_start = analysis_text.find("{")
                json_end = analysis_text.rfind("}") + 1
                json_text = analysis_text[json_start:json_end]
            else:
                raise ValueError("No JSON found in analysis")
            
            analysis_result = json.loads(json_text)
            
        except (json.JSONDecodeError, ValueError) as e:
            writer({
                "agent": "analysis",
                "status": "warning", 
                "message": f"JSON parsing failed: {e}, using fallback"
            })
            # Fallback analysis
            analysis_result = {
                "surface_materials": ["mixed"],
                "lighting_issues": ["general optimization needed"],
                "color_problems": ["needs enhancement"],
                "complex_problems": [],
                "editing_strategy": "imagemagick",
                "gemini_instructions": "",
                "imagemagick_command": "-brightness-contrast 5x10 -modulate 105,110,100",
                "editing_explanation": "Fallback to basic optimization",
                "remove_background": True,
                "optimization_priority": ["brightness", "contrast", "saturation"],
                "lens_corrections_applied": False
            }
        
        # Add metadata
        analysis_result["agent"] = "analysis"
        analysis_result["image_path"] = image_path
        
        # Debug output
        print(f"DEBUG: Analysis result strategy: {analysis_result.get('editing_strategy', 'NOT SET')}")
        print(f"DEBUG: Gemini instructions: {analysis_result.get('gemini_instructions', 'NOT SET')}")
        print(f"DEBUG: Full analysis result: {analysis_result}")
        
        writer({
            "agent": "analysis",
            "status": "complete",
            "strategy": analysis_result.get("editing_strategy", "unknown"),
            "message": f"Analysis complete - Strategy: {analysis_result.get('editing_strategy', 'unknown')}"
        })
        
        return analysis_result
        
    except Exception as e:
        error_msg = f"Analysis agent failed: {str(e)}"
        writer({
            "agent": "analysis",
            "status": "error",
            "message": error_msg
        })
        raise AgentError(error_msg)


async def gemini_edit_agent(image_path: str, analysis: Dict[str, Any]) -> str:
    """
    🎨 Gemini Edit Agent - Uses Gemini 2.5 Flash Image for advanced editing
    """
    writer = get_stream_writer()
    
    writer({
        "agent": "gemini_edit",
        "status": "editing", 
        "message": f"Applying AI-powered editing with Gemini 2.5 Flash Image"
    })
    
    gemini_instructions = analysis.get("gemini_instructions", "")
    print(f"DEBUG: Gemini agent received instructions: {gemini_instructions}")
    if not gemini_instructions:
        print("DEBUG: No Gemini instructions found!")
        raise AgentError("No Gemini editing instructions provided")
    
    try:
        print("🤖 Starting Gemini AI editing...")
        # Configure Gemini API
        configure_gemini()
        # Configure Gemini model
        model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        
        # Load image
        print(f"📁 Loading image: {Path(image_path).name}")
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
        
        print(f"📊 Image size: {len(image_data)} bytes")
        
        # Check if dust removal is needed
        needs_dust_removal = analysis.get("needs_dust_removal", False)
        dust_issues = analysis.get("dust_issues", [])
        
        # Create prompt for Gemini
        dust_removal_text = ""
        if needs_dust_removal and dust_issues:
            dust_removal_text = f"""
        IMPORTANT - Remove Visible Dust and Sensor Debris:
        Detected issues: {", ".join(dust_issues)}
        
        Dust Removal Guidelines:
        - Carefully remove dust spots and sensor debris without affecting product details
        - Clean surface dirt while preserving material textures
        - Ensure dust removal does not blur important product features
        - Focus on maintaining sharpness while removing debris
        """
        
        edit_prompt = f"""
        You are a professional product photography editor. Apply these specific improvements to this image:
        
        CRITICAL REQUIREMENT: You MUST preserve the ENTIRE image frame and dimensions. 
        DO NOT crop, trim, or remove ANY part of the image. 
        The output image MUST have the exact same dimensions and show ALL content from edge to edge.
        Return the COMPLETE, FULL IMAGE with all parts visible, including:
        - The entire top portion
        - The complete bottom portion including base/feet/stand
        - Full left and right sides
        - All edges and corners
        
        {dust_removal_text}
        
        {gemini_instructions}
        
        Focus on creating commercial-quality product photography suitable for e-commerce.
        Maintain product authenticity while enhancing visual appeal.
        Preserve important details while improving overall quality.
        REMINDER: Return the FULL, UNCROPPED image with identical dimensions to the input.
        """
        
        print("🚀 Sending to Gemini 2.5 Flash Image Preview...")
        # Send to Gemini for editing
        response = model.generate_content([
            edit_prompt,
            {
                "mime_type": get_image_media_type(image_path),
                "data": image_data
            }
        ])
        
        print("DEBUG: Received response from Gemini")
        print(f"DEBUG: Response type: {type(response)}")
        print(f"DEBUG: Response candidates: {len(response.candidates) if response.candidates else 0}")
        
        # Save edited image in same folder as original
        output_path = str(Path(image_path).parent / f"{Path(image_path).stem}-gemini-edited.webp")
        
        print("✅ Response received from Gemini")
        
        # Extract image from response - Gemini 2.5 Flash Image returns inline_data
        image_saved = False
        
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            print(f"DEBUG: Candidate content: {candidate.content}")
            print(f"DEBUG: Candidate parts: {len(candidate.content.parts) if candidate.content and candidate.content.parts else 0}")
            if candidate.content and candidate.content.parts:
                for i, part in enumerate(candidate.content.parts):
                    print(f"DEBUG: Part {i} type: {type(part)}")
                    print(f"DEBUG: Part {i} has inline_data: {hasattr(part, 'inline_data')}")
                    if hasattr(part, 'text'):
                        print(f"DEBUG: Part {i} text: {part.text[:200]}..." if len(str(part.text)) > 200 else f"DEBUG: Part {i} text: {part.text}")
                    if hasattr(part, 'inline_data') and part.inline_data:
                        print(f"✅ Found edited image data ({part.inline_data.mime_type}, {len(part.inline_data.data)} bytes)")
                        try:
                            # The data is already decoded binary image data, not base64!
                            image_data = part.inline_data.data
                            # Validate image format
                            if len(image_data) >= 4:
                                if image_data[:4] == b'\x89PNG':
                                    print("📸 Valid PNG format detected")
                                elif image_data[:3] == b'\xff\xd8\xff':
                                    print("📸 Valid JPEG format detected") 
                                elif image_data[:4] == b'RIFF':
                                    print("📸 Valid WebP format detected")
                                else:
                                    print("⚠️  Unknown image format, saving anyway")
                            
                            print(f"💾 Saving edited image ({len(image_data)} bytes)...")
                            with open(output_path, 'wb') as f:
                                bytes_written = f.write(image_data)
                                f.flush()
                            
                            # Verify the file was written correctly
                            import os
                            actual_file_size = os.path.getsize(output_path)
                            if actual_file_size == len(image_data):
                                print(f"✅ Successfully saved: {Path(output_path).name}")
                                image_saved = True
                            else:
                                print(f"❌ File size mismatch: expected {len(image_data)}, got {actual_file_size}")
                                raise Exception(f"File write verification failed")
                            break
                        except Exception as e:
                            print(f"❌ Error saving image: {e}")
                            continue
        
        if not image_saved:
            print("❌ No edited image found in Gemini response")
            print(f"DEBUG: Full response structure: {response}")
            raise AgentError("No edited image received from Gemini")
        
        # No transparency restoration needed - background removal happens after Gemini editing
        print("✅ Gemini editing complete - background removal will happen later if needed")
        
        writer({
            "agent": "gemini_edit",
            "status": "complete",
            "output": output_path,
            "message": f"Gemini editing complete: {Path(output_path).name}"
        })
        
        return output_path
        
    except Exception as e:
        error_msg = f"Gemini editing failed: {str(e)}"
        writer({
            "agent": "gemini_edit",
            "status": "error", 
            "message": error_msg
        })
        raise AgentError(error_msg)


async def imagemagick_optimization_agent(image_path: str, analysis: Dict[str, Any]) -> str:
    """
    ⚡ ImageMagick Optimization Agent - Traditional image processing
    """
    writer = get_stream_writer()
    
    writer({
        "agent": "imagemagick",
        "status": "optimizing",
        "message": f"Applying ImageMagick optimizations"
    })
    
    imagemagick_command = analysis.get("imagemagick_command", "-enhance")
    
    # Add lens correction only as fallback if not already applied by lens correction step
    needs_lens_correction = analysis.get("needs_lens_correction", False)
    lens_issues = analysis.get("lens_issues", [])
    lens_corrections_applied = analysis.get("lens_corrections_applied", False)
    
    if needs_lens_correction and lens_issues and not lens_corrections_applied:
        # Add basic lens correction parameters (fallback only)
        lens_corrections = []
        # Add virtual pixel method to prevent cropping
        lens_corrections.append("-virtual-pixel edge")
        if "barrel" in str(lens_issues).lower() or "pincushion" in str(lens_issues).lower():
            # Basic barrel/pincushion distortion correction using +distort to preserve canvas
            lens_corrections.append("+distort Barrel '0.0 -0.05 0.0'")
        if "vignetting" in str(lens_issues).lower():
            # Skip vignette command as it ADDS vignetting, not removes it
            # Instead use subtle brightening
            lens_corrections.append("-fill white -colorize 2%")
        
        if lens_corrections:
            imagemagick_command = f"{imagemagick_command} {' '.join(lens_corrections)}"
            writer({
                "agent": "imagemagick",
                "status": "info",
                "message": f"Adding fallback lens corrections: {', '.join(lens_issues)}"
            })
    
    # Add dust removal if needed
    needs_dust_removal = analysis.get("needs_dust_removal", False)
    dust_issues = analysis.get("dust_issues", [])
    
    if needs_dust_removal and dust_issues:
        # Add basic dust removal parameters
        dust_corrections = []
        if "spots" in dust_issues or "sensor_debris" in dust_issues:
            # Basic dust spot removal
            dust_corrections.append("-statistic median 3x3")
        if "surface_dirt" in dust_issues:
            # Surface dirt cleanup
            dust_corrections.append("-morphology close disk:1")
        
        if dust_corrections:
            imagemagick_command = f"{imagemagick_command} {' '.join(dust_corrections)}"
            writer({
                "agent": "imagemagick",
                "status": "info",
                "message": f"Adding dust corrections: {', '.join(dust_issues)}"
            })
    
    # Generate output path
    output_path = str(Path(image_path).parent / f"{Path(image_path).stem}-optimized.webp")
    
    try:
        # Build ImageMagick command with platform detection
        magick_cmd = get_imagemagick_command()
        
        # Check if ImageMagick is available
        if not magick_cmd:
            # ImageMagick not installed - skip this agent
            writer({
                "agent": "imagemagick",
                "status": "skipped",
                "message": "ImageMagick not available on this system, using Gemini AI editing only"
            })
            # Return original image path (as string, not dict)
            return image_path
        
        cmd_parts = imagemagick_command.strip().split()
        
        # Adjust command based on which ImageMagick binary is available
        if magick_cmd == 'convert':
            # Old ImageMagick format (v6 and earlier)
            full_cmd = [magick_cmd, image_path] + cmd_parts + ["-flatten", output_path]
        else:
            # New ImageMagick format (v7+)
            full_cmd = [magick_cmd, image_path] + cmd_parts + ["-flatten", output_path]
        
        writer({
            "agent": "imagemagick",
            "status": "processing",
            "command": " ".join(full_cmd[2:-2]),  # Show just the processing part
            "message": f"Executing: {' '.join(cmd_parts)}"
        })
        
        # Execute command
        result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and os.path.exists(output_path):
            writer({
                "agent": "imagemagick",
                "status": "complete",
                "output": output_path,
                "message": f"ImageMagick optimization complete: {Path(output_path).name}"
            })
            return output_path
        else:
            error_msg = f"ImageMagick failed: {result.stderr}"
            writer({
                "agent": "imagemagick",
                "status": "error",
                "message": error_msg
            })
            raise AgentError(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = "ImageMagick operation timed out"
        writer({"agent": "imagemagick", "status": "error", "message": error_msg})
        raise AgentError(error_msg)
    except Exception as e:
        error_msg = f"ImageMagick optimization failed: {str(e)}"
        writer({"agent": "imagemagick", "status": "error", "message": error_msg})
        raise AgentError(error_msg)


async def background_removal_agent(image_path: str, analysis: Dict[str, Any]) -> str:
    """
    🖼️ Background Removal Agent - Uses remove.bg API
    """
    writer = get_stream_writer()
    
    if not analysis.get("remove_background", False):
        writer({
            "agent": "background",
            "status": "skipped",
            "message": "Background removal not needed based on analysis"
        })
        return image_path
    
    api_key = os.getenv("REMOVE_BG_API_KEY")
    if not api_key:
        writer({
            "agent": "background",
            "status": "skipped", 
            "message": "Background removal skipped - no API key"
        })
        return image_path
    
    writer({
        "agent": "background",
        "status": "removing",
        "message": "Removing background with remove.bg API"
    })
    
    try:
        with open(image_path, 'rb') as image_file:
            response = requests.post(
                'https://api.remove.bg/v1.0/removebg',
                files={'image_file': image_file},
                data={'size': 'auto'},
                headers={'X-Api-Key': api_key},
                timeout=30
            )
        
        if response.status_code == 200:
            # Step 1: Save as PNG (native format from remove.bg)
            png_path = str(Path(image_path).parent / f"{Path(image_path).stem}-no-bg.png")
            with open(png_path, 'wb') as out_file:
                out_file.write(response.content)
            
            writer({
                "agent": "background",
                "status": "converting",
                "message": "Converting PNG to WebP for further processing"
            })
            
            # Step 2: Convert PNG to WebP using ImageMagick
            webp_path = str(Path(image_path).parent / f"{Path(image_path).stem}-no-bg.webp")
            try:
                import subprocess
                magick_cmd = get_imagemagick_command()
                
                # If ImageMagick not available, just use the PNG
                if not magick_cmd:
                    # Return PNG directly (Streamlit can display PNGs too)
                    webp_path = png_path  # Just use the PNG path
                    result_ok = True
                else:
                    cmd = [magick_cmd, png_path, "-quality", "95", webp_path]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    result_ok = (result.returncode == 0)
                    
                    if not result_ok:
                        # Fallback to PNG if conversion fails
                        webp_path = png_path
                        result_ok = True
                
                if result_ok:
                    writer({
                        "agent": "background",
                        "status": "complete",
                        "output": webp_path,
                        "message": f"Background removal and conversion complete: {Path(webp_path).name}"
                    })
                    return webp_path
                else:
                    # If conversion fails, return the PNG path
                    writer({
                        "agent": "background", 
                        "status": "warning",
                        "output": png_path,
                        "message": f"Background removal complete, WebP conversion failed - using PNG: {Path(png_path).name}"
                    })
                    return png_path
                    
            except Exception as convert_error:
                writer({
                    "agent": "background",
                    "status": "warning", 
                    "output": png_path,
                    "message": f"Background removal complete, conversion failed: {convert_error} - using PNG"
                })
                return png_path
        else:
            error_msg = f"Background removal failed: HTTP {response.status_code}"
            writer({"agent": "background", "status": "error", "message": error_msg})
            return image_path  # Return original if background removal fails
            
    except Exception as e:
        writer({
            "agent": "background",
            "status": "error",
            "message": f"Background removal error: {str(e)}"
        })
        return image_path  # Return original if fails


async def enhanced_qc_agent(image_path: str, original_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    ✅ Enhanced QC Agent - Evaluates results and decides on ImageMagick fallback
    """
    writer = get_stream_writer()
    
    writer({
        "agent": "qc",
        "status": "evaluating",
        "message": f"Quality control check for {Path(image_path).name}"
    })
    
    # Encode processed image
    image_base64 = encode_image_to_base64(image_path)
    media_type = get_image_media_type(image_path)
    
    # Enhanced QC prompt
    qc_prompt = f"""
    ENHANCED QUALITY CONTROL for e-commerce product image.
    
    Original analysis: {original_analysis.get('optimization_priority', [])}
    Applied strategy: {original_analysis.get('editing_strategy', 'unknown')}
    
    **STRICT EVALUATION CRITERIA**:
    
    1. **Digital Artifacts/Corruption**: 
       - ANY visible glitches, color bleeding, processing errors = FAIL
       - Pink/purple/cyan artifacts or unusual color patches = FAIL
       
    2. **Dust and Debris Removal**:
       - Check for remaining dust spots, sensor debris, or surface dirt
       - Ensure dust removal did not blur important product details
       - Verify that cleaning maintained material textures and sharpness
       
    3. **Professional Standards**:
       - Must look like professional product photography
       - Clean, sharp, commercial-grade appearance
       
    4. **Editing Quality**:
       - Natural-looking results (no over-processing)
       - Preserved product authenticity
       - Enhanced without looking artificial
       
    5. **Technical Excellence**:
       - Sharp focus, proper exposure
       - Clean edges, appropriate contrast
       - Material authenticity (chrome looks like chrome)
    
    **DECISION LOGIC**:
    - Score 9-10: Perfect, accept result
    - Score 7-8: Good but could benefit from ImageMagick refinement
    - Score 0-6: Poor quality, definitely needs ImageMagick backup
    
    Return JSON with:
    - passed: boolean (true if score 9+ AND no artifacts)
    - quality_score: number (0-10, be strict)
    - issues_found: [specific problems]
    - dust_removal_quality: string (excellent, good, fair, poor)
    - needs_imagemagick_fallback: boolean (recommend ImageMagick as backup)
    - imagemagick_suggestions: string (specific ImageMagick commands to try)
    - final_assessment: string (detailed explanation)
    
    **REMEMBER**: If Gemini editing looks artificial or over-processed, recommend ImageMagick fallback.
    """
    
    try:
        client = get_anthropic_client()
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64
                        }
                    },
                    {"type": "text", "text": qc_prompt}
                ]
            }]
        )
        
        qc_text = response.content[0].text
        
        try:
            # Parse QC response
            if "```json" in qc_text:
                json_start = qc_text.find("```json") + 7
                json_end = qc_text.find("```", json_start)
                json_text = qc_text[json_start:json_end].strip()
            elif "{" in qc_text:
                json_start = qc_text.find("{")
                json_end = qc_text.rfind("}") + 1
                json_text = qc_text[json_start:json_end]
            else:
                raise ValueError("No JSON found in QC response")
            
            qc_result = json.loads(json_text)
            
        except (json.JSONDecodeError, ValueError) as e:
            writer({
                "agent": "qc",
                "status": "warning",
                "message": f"QC parsing failed: {e}"
            })
            # Conservative fallback
            qc_result = {
                "passed": False,
                "quality_score": 5.0,
                "issues_found": ["qc_parsing_failed"],
                "needs_imagemagick_fallback": True,
                "imagemagick_suggestions": "-enhance -contrast",
                "final_assessment": "QC parsing failed, recommending ImageMagick fallback"
            }
        
        # Add metadata
        qc_result["agent"] = "qc"
        qc_result["image_path"] = image_path
        
        status = "passed" if qc_result.get("passed", False) else "failed"
        fallback_needed = qc_result.get("needs_imagemagick_fallback", False)
        
        writer({
            "agent": "qc",
            "status": status,
            "quality_score": qc_result.get("quality_score", 0),
            "fallback_recommended": fallback_needed,
            "message": f"QC {status} - Score: {qc_result.get('quality_score', 0)}/10"
        })
        
        return qc_result
        
    except Exception as e:
        error_msg = f"QC agent failed: {str(e)}"
        writer({"agent": "qc", "status": "error", "message": error_msg})
        raise AgentError(error_msg)


# Export the enhanced agents
__all__ = [
    'enhanced_analysis_agent',
    'gemini_edit_agent', 
    'imagemagick_optimization_agent',
    'background_removal_agent',
    'enhanced_qc_agent',
    'AgentError'
]