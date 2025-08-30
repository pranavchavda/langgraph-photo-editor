"""
Agentic Photo Editor - Individual AI Agents (Fixed Version)
Each agent handles a specific aspect of photo processing
"""

import base64
import os
import subprocess
import json
import requests
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image
import tempfile

from anthropic import AsyncAnthropic
from langgraph.config import get_stream_writer


class AgentError(Exception):
    """Base exception for agent errors"""
    pass


def encode_image_to_base64(image_path: str) -> str:
    """Encode image to base64 for Claude vision API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def get_image_media_type(image_path: str) -> str:
    """Get media type for Claude vision API"""
    ext = Path(image_path).suffix.lower()
    if ext == '.jpg' or ext == '.jpeg':
        return "image/jpeg"
    elif ext == '.png':
        return "image/png" 
    elif ext == '.webp':
        return "image/webp"
    else:
        return "image/jpeg"  # default


async def analysis_agent(image_path: str) -> Dict[str, Any]:
    """Analyzes image and determines optimization strategy"""
    writer = get_stream_writer()
    writer({
        "agent": "analysis", 
        "status": "analyzing", 
        "message": "Identifying surfaces, lighting, and optimization needs..."
    })
    
    try:
        # Initialize Claude
        client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Encode image
        image_base64 = encode_image_to_base64(image_path)
        media_type = get_image_media_type(image_path)
        
        # Check for custom instructions from chat mode
        custom_instructions = os.getenv("CUSTOM_PROCESSING_INSTRUCTIONS", "")
        custom_adjustments = os.getenv("CUSTOM_ADJUSTMENTS", "{}")
        
        try:
            custom_prefs = json.loads(custom_adjustments) if custom_adjustments != "{}" else {}
        except:
            custom_prefs = {}

        # Build analysis prompt with custom instructions
        base_prompt = """
        Analyze this product image for photo editing optimization. Focus on:

        1. **Surface Materials**: Identify chrome, stainless steel, matte surfaces, glass, plastic
        2. **Lighting Issues**: Harsh shadows, overexposure, underexposure, uneven lighting
        3. **Color Quality**: Saturation levels, color cast issues, vibrancy needs
        4. **Background**: Current background type and removal needs
        5. **Specific Problems**: Reflections, blown highlights, dark shadows, color accuracy

        Return analysis as JSON with these fields:
        - surface_materials: [list of materials detected]  
        - lighting_issues: [list of specific problems]
        - color_problems: [list of color issues]
        - background_type: string description
        - optimization_needs: [priority-ordered list of adjustments needed]
        - imagemagick_command: string (complete ImageMagick parameters like "-trim -brightness-contrast 10x5 -modulate 105,110,100")
        - remove_background: boolean
        - command_explanation: string (brief explanation of what the ImageMagick command will do)
        - special_considerations: [any material-specific notes]

        Be specific and actionable in your analysis.
        
        **IMAGEMAGICK REFERENCE** - Use any combination of these operations:
        
        **Core Operations:**
        - "-trim" (remove whitespace borders)  
        - "-brightness-contrast BxC" (adjust brightness B and contrast C, e.g., "10x5")
        - "-modulate B,S,H" (brightness B%, saturation S%, hue H%, e.g., "105,110,100")
        - "-gamma G" (gamma correction, e.g., "1.2")
        - "-enhance" (enhance image)
        - "-normalize" (normalize contrast)
        - "-unsharp RxS+G+T" (unsharp mask, e.g., "0x1.5+1.0+0.0")
        - "-border N" (add N pixel border)
        - "-bordercolor color" (border color)
        - "-blur geometry" (reduce noise and detail)
        - "-sharpen geometry" (increase sharpness)
        - "-gaussian-blur geometry" (smooth blur)
        - "-adaptive-blur geometry" (edge-preserving blur)
        - "-adaptive-sharpen geometry" (edge-preserving sharpen)
        - "-contrast" (enhance contrast)
        - "-level value" (adjust contrast levels)
        - "-auto-level" (automatic level adjustment)
        - "-auto-gamma" (automatic gamma correction)
        - "-despeckle" (reduce speckles/noise)
        - "-noise geometry" (add/reduce noise)
        - "-quality N" (compression quality 1-100)
        
        **Advanced Operations:**
        - "-bilateral-blur geometry" (edge-preserving noise reduction)
        - "-clahe geometry" (contrast limited adaptive histogram equalization)
        - "-contrast-stretch geometry" (improve contrast by stretching intensity)
        - "-linear-stretch geometry" (contrast stretch with saturation)
        - "-local-contrast geometry" (enhance local contrast)
        - "-colorspace type" (change colorspace: RGB, sRGB, etc.)
        - "-clamp" (keep pixel values in valid range)
        
        Example: "-trim -brightness-contrast 5x10 -modulate 102,115,100 -border 20 -bordercolor white"
        """
        
        # Add custom instructions if provided
        if custom_instructions:
            analysis_prompt = base_prompt + f"""
            
        **CRITICAL CUSTOM INSTRUCTIONS**: {custom_instructions}
        
        FOLLOW THESE USER PREFERENCES PRECISELY:
        - If user wants "trim", "crop", or "remove whitespace" -> include "-trim" in imagemagick_command
        - If user wants "darker", "natural", or "less bright" -> use negative brightness values
        - If user wants "brighter" or "more vibrant" -> use positive brightness and saturation
        - If user wants "natural" or "less processed" -> use minimal adjustments
        - The custom instructions OVERRIDE default analysis - prioritize user intent
        - Be conservative - better to under-adjust than over-adjust
        """
        else:
            analysis_prompt = base_prompt
            
        # Apply custom adjustment preferences if provided
        if custom_prefs:
            brightness_pref = custom_prefs.get('brightness_preference', 0)
            contrast_pref = custom_prefs.get('contrast_preference', 0) 
            saturation_pref = custom_prefs.get('saturation_preference', 0)
            
            if any([brightness_pref, contrast_pref, saturation_pref]):
                analysis_prompt += f"""
                
        **CUSTOM PREFERENCES**: 
        - Brightness preference: {brightness_pref:+d} (bias your brightness_adjustment toward this)
        - Contrast preference: {contrast_pref:+d} (bias your contrast_adjustment toward this)
        - Saturation preference: {saturation_pref:+d} (bias your saturation_adjustment toward this)
        """
        
        # Check for QC feedback from previous retry attempts
        qc_feedback = os.getenv("QC_FEEDBACK_JSON", "{}")
        try:
            qc_data = json.loads(qc_feedback) if qc_feedback != "{}" else {}
            if qc_data:
                correction_notes = qc_data.get('correction_notes', [])
                critical_failures = qc_data.get('critical_failures', [])
                retry_attempt = qc_data.get('retry_attempt', 1)
                
                analysis_prompt += f"""
                
        **QC RETRY FEEDBACK** (Attempt {retry_attempt}): 
        Critical Failures: {critical_failures}
        Correction Notes: {correction_notes}
        
        **IMPORTANT**: Apply these corrections in your ImageMagick command:
        {chr(10).join(['- ' + note for note in correction_notes])}
        
        Be MUCH more conservative with adjustments to avoid artifacts and quality issues.
        """
        except:
            pass  # Ignore JSON parsing errors

        response = await client.messages.create(
            model="claude-sonnet-4-20250514",  # Claude Sonnet 4
            max_tokens=1000,
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
        
        # Parse the JSON response
        analysis_text = response.content[0].text
        
        # Extract JSON from response (handle both markdown and raw JSON)
        try:
            if "```json" in analysis_text:
                # Markdown formatted JSON
                json_start = analysis_text.find("```json") + 7
                json_end = analysis_text.find("```", json_start)
                json_text = analysis_text[json_start:json_end].strip()
            elif "{" in analysis_text and "}" in analysis_text:
                # Raw JSON - find the complete JSON object
                json_start = analysis_text.find("{")
                json_end = analysis_text.rfind("}") + 1
                json_text = analysis_text[json_start:json_end].strip()
            else:
                raise ValueError("No JSON found in response")
            
            analysis = json.loads(json_text)
            
            # Validate that we got the expected fields
            if not analysis.get("imagemagick_command"):
                raise ValueError("Missing imagemagick_command field")
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback analysis if JSON parsing fails
            writer({
                "agent": "analysis", 
                "status": "warning", 
                "message": f"JSON parsing failed, using fallback analysis: {e}"
            })
            # Use much more conservative fallback values
            analysis = {
                "surface_materials": ["unknown"],
                "lighting_issues": ["needs_analysis"],
                "color_problems": ["needs_analysis"],
                "background_type": "unknown",
                "optimization_needs": ["minimal_adjustments"],
                "imagemagick_command": "-modulate 102,105,100",  # Very minimal adjustments
                "remove_background": True,
                "command_explanation": "Minimal brightness and saturation boost (fallback)",
                "special_considerations": ["fallback_analysis_used", "conservative_adjustments"]
            }
        
        # Add metadata
        analysis["image_path"] = image_path
        analysis["agent"] = "analysis"
        analysis["timestamp"] = asyncio.get_event_loop().time()
        
        writer({
            "agent": "analysis", 
            "status": "complete", 
            "analysis": analysis,
            "message": f"Analysis complete - {len(analysis.get('optimization_needs', []))} optimizations identified"
        })
        
        return analysis
        
    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        writer({
            "agent": "analysis", 
            "status": "error", 
            "message": error_msg
        })
        raise AgentError(error_msg)


async def background_agent(image_path: str, analysis: Dict[str, Any]) -> str:
    """Removes background using remove.bg API"""
    writer = get_stream_writer()
    writer({
        "agent": "background", 
        "status": "processing", 
        "message": "Removing background with AI..."
    })
    
    try:
        # Check if background removal is needed
        if not analysis.get("remove_background", True):
            writer({
                "agent": "background", 
                "status": "skipped", 
                "message": "Background removal not needed per analysis"
            })
            return image_path
        
        api_key = os.getenv("REMOVE_BG_API_KEY")
        if not api_key:
            raise AgentError("REMOVE_BG_API_KEY not set")
        
        # Prepare output path (always WebP for transparency)
        input_path = Path(image_path)
        output_path = input_path.parent / f"{input_path.stem}_bg_removed.webp"
        
        # Call remove.bg API
        with open(image_path, 'rb') as image_file:
            response = requests.post(
                'https://api.remove.bg/v1.0/removebg',
                files={'image_file': image_file},
                data={'size': 'auto', 'format': 'webp'},
                headers={'X-Api-Key': api_key},
                timeout=30
            )
        
        if response.status_code != 200:
            error_msg = f"remove.bg API failed: {response.status_code} - {response.text}"
            raise AgentError(error_msg)
        
        # Save result
        with open(output_path, 'wb') as out_file:
            out_file.write(response.content)
        
        writer({
            "agent": "background", 
            "status": "complete", 
            "path": str(output_path),
            "message": f"Background removed successfully"
        })
        
        return str(output_path)
        
    except Exception as e:
        error_msg = f"Background removal failed: {str(e)}"
        writer({
            "agent": "background", 
            "status": "error", 
            "message": error_msg
        })
        raise AgentError(error_msg)


async def optimization_agent(image_path: str, analysis: Dict[str, Any]) -> str:
    """Applies custom optimizations based on analysis"""
    writer = get_stream_writer()
    writer({
        "agent": "optimization", 
        "status": "processing", 
        "message": "Applying intelligent optimizations..."
    })
    
    try:
        # Prepare output path
        input_path = Path(image_path)
        output_path = input_path.parent / f"{input_path.stem}_optimized.webp"
        
        # Get the ImageMagick command from analysis
        imagemagick_params = analysis.get("imagemagick_command", "-modulate 100,100,100")  # No-op fallback
        command_explanation = analysis.get("command_explanation", "No adjustments")
        
        # Build complete ImageMagick command
        # Split the parameters and build the command list
        if imagemagick_params.strip():
            param_list = imagemagick_params.strip().split()
        else:
            param_list = []
        
        magick_cmd = ["magick", str(image_path)] + param_list + ["-flatten", str(output_path)]
        
        writer({
            "agent": "optimization", 
            "status": "processing", 
            "message": f"Executing: {command_explanation}"
        })
        
        # Execute ImageMagick command
        result = subprocess.run(
            magick_cmd, 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        
        if result.returncode != 0:
            error_msg = f"ImageMagick failed: {result.stderr}"
            raise AgentError(error_msg)
        
        # Verify output file was created
        if not output_path.exists():
            raise AgentError("Optimization output file was not created")
        
        writer({
            "agent": "optimization", 
            "status": "complete", 
            "commands": magick_cmd,
            "imagemagick_params": imagemagick_params,
            "path": str(output_path),
            "message": f"ImageMagick: {imagemagick_params}"
        })
        
        return str(output_path)
        
    except Exception as e:
        error_msg = f"Optimization failed: {str(e)}"
        writer({
            "agent": "optimization", 
            "status": "error", 
            "message": error_msg
        })
        raise AgentError(error_msg)


async def qc_agent(image_path: str, original_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Quality control validation and approval"""
    writer = get_stream_writer()
    writer({
        "agent": "qc", 
        "status": "validating", 
        "message": "Checking quality standards..."
    })
    
    try:
        # Initialize Claude for QC analysis
        client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Encode processed image
        image_base64 = encode_image_to_base64(image_path)
        media_type = get_image_media_type(image_path)
        
        # QC prompt comparing to original analysis
        qc_prompt = f"""
        CRITICAL QUALITY CONTROL CHECK for e-commerce product image.
        
        Original analysis: {original_analysis.get('optimization_needs', [])}
        Applied command: {original_analysis.get('imagemagick_command', 'none')}
        
        **STRICT EVALUATION CRITERIA** - FAIL if ANY major issue exists:
        
        1. **Digital Artifacts/Corruption**: 
           - Any visible glitches, color bleeding, or digital noise
           - Pink/purple/cyan artifacts or unusual color patches
           - Pixelation, banding, or processing errors
           
        2. **Professional Standards**:
           - Must look like professional product photography
           - Clean, sharp, commercial-grade appearance
           - No amateur or processed look
           
        3. **Color Accuracy**:
           - Natural, realistic colors for materials (chrome, steel, etc.)
           - No unnatural color casts or oversaturation
           - Materials must look authentic
           
        4. **Technical Quality**:
           - Sharp focus on product details
           - Proper exposure without blown highlights
           - Clean edges and proper contrast
           
        5. **Background/Composition**:
           - Clean background without artifacts
           - Proper product positioning
           - Professional lighting
        
        **CRITICAL**: Look VERY carefully for ANY unusual colors, patches, or artifacts:
        - Pink/purple/cyan patches = CORRUPTION 
        - Color bleeding/smearing = PROCESSING ERROR
        - Unusual color patches that don't belong = ARTIFACTS
        - Any digital noise or glitches = FAILURE
        
        **SCORING**: Be RUTHLESSLY strict - this is for commercial sales:
        - ANY visible artifacts/corruption = AUTOMATIC 0-2 score
        - 9-10: Perfect commercial quality (no artifacts whatsoever)
        - 7-8: Good but minor issues (no artifacts)
        - 5-6: Noticeable problems, needs work  
        - 3-4: Poor quality, major issues
        - 0-2: Digital corruption/artifacts present - UNACCEPTABLE
        
        Return JSON with:
        - passed: boolean (ONLY true if score 9+ AND zero artifacts detected)
        - quality_score: number (0-10, be HARSH - any artifacts = 0-2)
        - issues_found: [specific problems - be detailed]
        - critical_failures: [any deal-breaker issues - describe exact artifacts seen]
        - improvements: {{specific ImageMagick parameter suggestions}}
        - final_assessment: string (detailed explanation focusing on artifacts)
        
        **ABSOLUTE RULE**: ANY pink/purple patches, color bleeding, or unusual color artifacts = SCORE 0-2 + AUTOMATIC FAIL
        """

        response = await client.messages.create(
            model="claude-sonnet-4-20250514",  # Claude Sonnet 4
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
        
        # Parse QC response
        qc_text = response.content[0].text
        
        try:
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
            # Fallback QC result
            writer({
                "agent": "qc", 
                "status": "warning", 
                "message": f"QC JSON parsing failed, using fallback: {e}"
            })
            qc_result = {
                "passed": False,  # Default to FAIL if we can't parse - safer for QC
                "quality_score": 4.0,
                "issues_found": ["qc_parsing_failed"],
                "critical_failures": ["qc_system_error"],
                "improvements": {},
                "final_assessment": "QC analysis failed, defaulting to FAIL for safety"
            }
        
        # Add metadata
        qc_result["image_path"] = image_path
        qc_result["agent"] = "qc"
        qc_result["timestamp"] = asyncio.get_event_loop().time()
        
        status = "passed" if qc_result.get("passed", False) else "failed"
        score = qc_result.get("quality_score", 0)
        
        writer({
            "agent": "qc", 
            "status": status, 
            "quality_score": score,
            "passed": qc_result.get("passed", False),
            "message": f"QC {status} - Score: {score}/10"
        })
        
        return qc_result
        
    except Exception as e:
        error_msg = f"Quality control failed: {str(e)}"
        writer({
            "agent": "qc", 
            "status": "error", 
            "message": error_msg
        })
        raise AgentError(error_msg)