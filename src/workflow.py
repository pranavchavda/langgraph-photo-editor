"""
Agentic Photo Editor - LangGraph Workflow Orchestrator
Modern LangGraph functional API implementation
"""

from typing import TypedDict, Annotated, Dict, Any, Optional
from pathlib import Path
import operator
import asyncio

from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer

from .agents import (
    analysis_agent,
    background_agent, 
    optimization_agent,
    qc_agent,
    AgentError
)


class PhotoProcessingState(TypedDict):
    """State for the photo processing workflow"""
    input_image_path: str
    analysis_report: Dict[str, Any]
    background_removed_path: str
    optimized_image_path: str
    qc_report: Dict[str, Any]
    final_image_path: str
    retry_count: int
    processing_logs: Annotated[list, operator.add]
    error_messages: Annotated[list, operator.add]


# Initialize checkpointer for state persistence
checkpointer = InMemorySaver()


@task
async def run_analysis_agent(image_path: str) -> Dict[str, Any]:
    """🔍 Task wrapper for analysis agent"""
    try:
        return await analysis_agent(image_path)
    except AgentError as e:
        raise


@task  
async def run_background_agent(image_path: str, analysis: Dict[str, Any]) -> str:
    """🎨 Task wrapper for background removal agent"""
    try:
        return await background_agent(image_path, analysis)
    except AgentError as e:
        raise


@task
async def run_optimization_agent(image_path: str, analysis: Dict[str, Any]) -> str:
    """⚡ Task wrapper for optimization agent"""
    try:
        return await optimization_agent(image_path, analysis)
    except AgentError as e:
        raise


@task
async def run_qc_agent(image_path: str, original_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """✅ Task wrapper for quality control agent"""
    try:
        return await qc_agent(image_path, original_analysis)
    except AgentError as e:
        raise


@entrypoint(checkpointer=checkpointer)
async def agentic_photo_processor(
    inputs: Dict[str, Any], 
    *, 
    previous: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """🤖 Complete 4-agent photo processing workflow with retry logic"""
    
    # Initialize stream writer
    writer = get_stream_writer()
    
    # Initialize or restore state
    image_path = inputs["image_path"]
    retry_count = (previous or {}).get("retry_count", 0)
    refined_analysis = inputs.get("analysis")  # For retries
    
    writer({
        "workflow": "started",
        "image_path": image_path,
        "retry_count": retry_count,
        "message": f"Starting agentic processing for {Path(image_path).name}"
    })
    
    try:
        # Agent 1: Analysis (use refined analysis for retries)
        if refined_analysis:
            writer({
                "agent": "analysis",
                "status": "using_refined", 
                "message": "Using refined analysis from QC feedback"
            })
            analysis = refined_analysis
        else:
            analysis = await run_analysis_agent(image_path)
        
        # Agent 2: Optimization (first, to avoid background removal artifacts)
        optimized_path = await run_optimization_agent(image_path, analysis)
        
        # Agent 3: Background Removal (last, to avoid introducing artifacts)
        if analysis.get("remove_background", True):
            bg_removed_path = await run_background_agent(optimized_path, analysis)
            final_processed_path = bg_removed_path
        else:
            final_processed_path = optimized_path
        
        # Agent 4: Quality Control
        qc_result = await run_qc_agent(final_processed_path, analysis)
        
        # Check QC results
        if qc_result.get("passed", False):
            writer({
                "workflow": "success",
                "final_image": final_processed_path,
                "quality_score": qc_result.get("quality_score", 0),
                "message": f"✅ Processing complete - Quality score: {qc_result.get('quality_score', 0)}/10"
            })
            
            return entrypoint.final(
                value={
                    "final_image": final_processed_path, 
                    "qc_passed": True,
                    "quality_score": qc_result.get("quality_score", 0),
                    "retry_count": retry_count
                },
                save={
                    "analysis": analysis,
                    "final_path": final_processed_path,
                    "qc_report": qc_result,
                    "retry_count": retry_count,
                    "processing_complete": True
                }
            )
        
        # QC Failed - attempt retry with refinements
        if retry_count < 2:  # Max 2 retries
            writer({
                "workflow": "retry",
                "attempt": retry_count + 1,
                "issues": qc_result.get("issues_found", []),
                "message": f"🔄 QC failed, retrying with improvements (attempt {retry_count + 1}/2)"
            })
            
            # Apply QC improvements to analysis
            improvements = qc_result.get("improvements", {})
            issues = qc_result.get("issues_found", [])
            critical_failures = qc_result.get("critical_failures", [])
            
            refined_analysis = {**analysis}
            
            # Generate corrective ImageMagick command based on QC feedback
            correction_notes = []
            if "digital_artifacts" in critical_failures or "corruption" in str(critical_failures):
                correction_notes.append("reduce processing intensity to avoid artifacts")
            if "oversaturation" in str(issues):
                correction_notes.append("reduce saturation")
            if "overexposure" in str(issues):
                correction_notes.append("reduce brightness")
            if "harsh_shadows" in str(issues):
                correction_notes.append("improve gamma and contrast balance")
            
            # Add correction guidance to analysis
            refined_analysis["qc_feedback"] = {
                "issues": issues,
                "critical_failures": critical_failures,
                "correction_notes": correction_notes,
                "retry_attempt": retry_count + 1
            }
            
            # Set QC feedback in environment for analysis agent
            import os
            import json
            os.environ["QC_FEEDBACK_JSON"] = json.dumps(refined_analysis["qc_feedback"])
            
            # Recursive retry with refined analysis
            return entrypoint.final(
                value=await agentic_photo_processor(
                    {
                        "image_path": image_path, 
                        "analysis": refined_analysis
                    }
                ),
                save={"retry_count": retry_count + 1}
            )
        
        # Max retries reached - return best attempt
        writer({
            "workflow": "max_retries",
            "final_image": optimized_path,
            "quality_score": qc_result.get("quality_score", 0),
            "message": f"⚠️  Max retries reached - Using best attempt (Score: {qc_result.get('quality_score', 0)}/10)"
        })
        
        return entrypoint.final(
            value={
                "final_image": optimized_path, 
                "qc_passed": False, 
                "max_retries": True,
                "quality_score": qc_result.get("quality_score", 0),
                "retry_count": retry_count,
                "issues": qc_result.get("issues_found", [])
            },
            save={
                "retry_count": retry_count, 
                "final_attempt": optimized_path,
                "qc_report": qc_result
            }
        )
        
    except Exception as e:
        error_msg = f"Workflow failed: {str(e)}"
        writer({
            "workflow": "error",
            "error": error_msg,
            "message": f"❌ Critical error in processing pipeline"
        })
        
        return entrypoint.final(
            value={
                "error": error_msg,
                "failed": True,
                "retry_count": retry_count
            },
            save={
                "error": error_msg,
                "failed_at": asyncio.get_event_loop().time()
            }
        )


# Convenience function for batch processing
async def process_image_batch(
    image_paths: list[str],
    output_dir: Optional[str] = None,
    max_concurrent: int = 3
) -> Dict[str, Any]:
    """Process multiple images concurrently with the agentic workflow"""
    
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
    
    # Semaphore to limit concurrent processing
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_single_image(image_path: str) -> Dict[str, Any]:
        async with semaphore:
            config = {"configurable": {"thread_id": str(Path(image_path).stem)}}
            
            try:
                result = await agentic_photo_processor.ainvoke(
                    {"image_path": image_path},
                    config=config
                )
                return {"image_path": image_path, "result": result, "status": "success"}
                
            except Exception as e:
                return {"image_path": image_path, "error": str(e), "status": "failed"}
    
    # Process all images concurrently
    tasks = [process_single_image(img_path) for img_path in image_paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Summarize results
    successful = [r for r in results if isinstance(r, dict) and r.get("status") == "success"]
    failed = [r for r in results if isinstance(r, dict) and r.get("status") == "failed"]
    exceptions = [r for r in results if isinstance(r, Exception)]
    
    return {
        "total_processed": len(image_paths),
        "successful": len(successful),
        "failed": len(failed) + len(exceptions),
        "results": results,
        "summary": {
            "success_rate": len(successful) / len(image_paths) * 100,
            "processing_complete": True
        }
    }