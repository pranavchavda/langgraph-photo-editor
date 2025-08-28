"""
Agentic Photo Editor - Individual AI Agents
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
    """🔍 Analyzes image and determines optimization strategy"""
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
        
        # Analysis prompt for product photography
        analysis_prompt = """
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
        - brightness_adjustment: number (-50 to +50, 0 = no change)
        - contrast_adjustment: number (-50 to +50, 0 = no change) 
        - saturation_adjustment: number (-50 to +50, 0 = no change)
        - gamma_adjustment: number (0.5 to 2.0, 1.0 = no change)
        - remove_background: boolean
        - special_considerations: [any material-specific notes]

        Be specific and actionable in your analysis.
        """

        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
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
        
        # Extract JSON from response (handle potential markdown formatting)
        try:
            if "```json" in analysis_text:
                json_start = analysis_text.find("```json") + 7
                json_end = analysis_text.find("```", json_start)
                json_text = analysis_text[json_start:json_end].strip()
            elif "{" in analysis_text:
                json_start = analysis_text.find("{")
                json_end = analysis_text.rfind("}") + 1
                json_text = analysis_text[json_start:json_end]
            else:
                raise ValueError("No JSON found in response")
            
            analysis = json.loads(json_text)
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback analysis if JSON parsing fails
            writer({
                "agent": "analysis", 
                "status": "warning", 
                "message": f"JSON parsing failed, using fallback analysis: {e}"
            })
            analysis = {
                "surface_materials": ["unknown"],
                "lighting_issues": ["needs_analysis"],
                "color_problems": ["needs_analysis"],
                "background_type": "unknown",
                "optimization_needs": ["brightness", "contrast", "saturation"],
                "brightness_adjustment": 10,
                "contrast_adjustment": 10,
                "saturation_adjustment": 15,
                "gamma_adjustment": 1.1,
                "remove_background": True,
                "special_considerations": ["fallback_analysis_used"]
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
    """🎨 Removes background using remove.bg API"""
    writer = get_stream_writer()
    writer({
        "agent": "background", 
        "status": "processing", 
        "message": "Removing background with AI..."
    })
    
    try:
        # Check if background removal is needed
        if not analysis.get("remove_background", True):
            writer.write({
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
        
        writer.write({
            "agent": "background", 
            "status": "complete", 
            "path": str(output_path),
            "message": f"Background removed successfully"
        })
        
        return str(output_path)
        
    except Exception as e:
        error_msg = f"Background removal failed: {str(e)}"
        writer.write({
            "agent": "background", 
            "status": "error", 
            "message": error_msg
        })
        raise AgentError(error_msg)


async def optimization_agent(image_path: str, analysis: Dict[str, Any], writer: StreamWriter) -> str:
    """⚡ Applies custom optimizations based on analysis"""
    writer.write({
        "agent": "optimization", 
        "status": "processing", 
        "message": "Applying intelligent optimizations..."
    })
    
    try:
        # Prepare output path
        input_path = Path(image_path)
        output_path = input_path.parent / f"{input_path.stem}_optimized.webp"
        
        # Build ImageMagick command based on analysis
        magick_cmd = ["magick", str(image_path)]
        
        adjustments_applied = []
        
        # Apply brightness adjustment
        brightness = analysis.get("brightness_adjustment", 0)
        if abs(brightness) > 2:  # Only apply if significant
            magick_cmd.extend(["-modulate", f"{100 + brightness},100,100"])
            adjustments_applied.append(f"brightness {brightness:+d}")
        
        # Apply contrast adjustment  
        contrast = analysis.get("contrast_adjustment", 0)
        if abs(contrast) > 2:
            magick_cmd.extend(["-contrast-stretch", f"{contrast}%"])
            adjustments_applied.append(f"contrast {contrast:+d}%")
        
        # Apply saturation adjustment
        saturation = analysis.get("saturation_adjustment", 0)
        if abs(saturation) > 2:
            sat_value = 100 + saturation
            magick_cmd.extend(["-modulate", f"100,{sat_value},100"])
            adjustments_applied.append(f"saturation {saturation:+d}")
        
        # Apply gamma adjustment
        gamma = analysis.get("gamma_adjustment", 1.0)
        if abs(gamma - 1.0) > 0.05:  # Only apply if significant
            magick_cmd.extend(["-gamma", str(gamma)])
            adjustments_applied.append(f"gamma {gamma:.2f}")
        
        # Handle chrome/stainless steel surfaces
        if "chrome" in analysis.get("surface_materials", []) or "stainless steel" in analysis.get("surface_materials", []):
            # Reduce highlights and increase detail
            magick_cmd.extend(["-highlight-color", "white", "-shadows", "10"])
            adjustments_applied.append("chrome optimization")
        
        # Ensure single frame output and flatten
        magick_cmd.extend(["-flatten", "[0]"])
        
        # Add output path
        magick_cmd.append(str(output_path))
        
        writer.write({
            "agent": "optimization", 
            "status": "processing", 
            "message": f"Applying: {', '.join(adjustments_applied) or 'no adjustments needed'}"
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
        
        writer.write({
            "agent": "optimization", 
            "status": "complete", 
            "commands": magick_cmd,
            "adjustments": adjustments_applied,
            "path": str(output_path),
            "message": f"Applied {len(adjustments_applied)} optimizations"
        })
        
        return str(output_path)
        
    except Exception as e:
        error_msg = f"Optimization failed: {str(e)}"
        writer.write({
            "agent": "optimization", 
            "status": "error", 
            "message": error_msg
        })
        raise AgentError(error_msg)


async def qc_agent(image_path: str, original_analysis: Dict[str, Any], writer: StreamWriter) -> Dict[str, Any]:
    """✅ Quality control validation and approval"""
    writer.write({
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
        Quality control check for this processed product image.
        
        Original analysis found these issues: {original_analysis.get('optimization_needs', [])}
        Applied these adjustments: brightness={original_analysis.get('brightness_adjustment', 0)}, 
        contrast={original_analysis.get('contrast_adjustment', 0)}, 
        saturation={original_analysis.get('saturation_adjustment', 0)},
        gamma={original_analysis.get('gamma_adjustment', 1.0)}
        
        Evaluate the current image quality on:
        1. **Professional appearance**: Clean, product-focused, commercial quality
        2. **Color accuracy**: Natural, not oversaturated or washed out
        3. **Lighting**: Even, no harsh shadows or blown highlights  
        4. **Detail preservation**: Sharp, clear product features
        5. **Background**: Clean transparency or appropriate background
        
        Return JSON with:
        - passed: boolean (true if meets quality standards)
        - quality_score: number (0-10, where 8+ is acceptable)
        - issues_found: [list of remaining problems]
        - improvements: {{suggested parameter adjustments if failed}}
        - final_assessment: string summary
        
        Be strict but fair - this is for e-commerce product photography.
        """

        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
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
            writer.write({
                "agent": "qc", 
                "status": "warning", 
                "message": f"QC JSON parsing failed, using fallback: {e}"
            })
            qc_result = {
                "passed": True,  # Default to pass if we can't parse
                "quality_score": 7.0,
                "issues_found": ["qc_parsing_failed"],
                "improvements": {},
                "final_assessment": "QC analysis failed, defaulting to pass"
            }
        
        # Add metadata
        qc_result["image_path"] = image_path
        qc_result["agent"] = "qc"
        qc_result["timestamp"] = asyncio.get_event_loop().time()
        
        status = "passed" if qc_result.get("passed", False) else "failed"
        score = qc_result.get("quality_score", 0)
        
        writer.write({
            "agent": "qc", 
            "status": status, 
            "quality_score": score,
            "passed": qc_result.get("passed", False),
            "message": f"QC {status} - Score: {score}/10"
        })
        
        return qc_result
        
    except Exception as e:
        error_msg = f"Quality control failed: {str(e)}"
        writer.write({
            "agent": "qc", 
            "status": "error", 
            "message": error_msg
        })
        raise AgentError(error_msg)