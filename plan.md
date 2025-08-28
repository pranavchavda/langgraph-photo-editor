  CLI-First Agentic Photo Editor with LangGraph

  Phase 1: Build the Agency (CLI)

  # Modern LangGraph functional API approach
  from typing import TypedDict, Annotated
  from langchain_core.messages import BaseMessage, add_messages
  from langgraph.func import entrypoint, task
  from langgraph.checkpoint.memory import InMemorySaver
  from langgraph.types import StreamWriter
  import operator

  class PhotoProcessingState(TypedDict):
      input_image_path: str
      analysis_report: dict
      background_removed_path: str
      optimized_image_path: str
      qc_report: dict
      final_image_path: str
      retry_count: int
      processing_logs: Annotated[list, operator.add]

  @task
  async def analysis_agent(image_path: str, writer: StreamWriter) -> dict:
      """🔍 Analyzes image and determines optimization strategy"""
      writer.write({"agent": "analysis", "status": "analyzing", "message": "Identifying surfaces and issues..."})

      # Claude vision analysis
      analysis = await claude_analyze_image(image_path)

      writer.write({"agent": "analysis", "status": "complete", "analysis": analysis})
      return analysis

  @task  
  async def background_agent(image_path: str, analysis: dict, writer: StreamWriter) -> str:
      """🎨 Removes background using remove.bg API"""
      writer.write({"agent": "background", "status": "processing", "message": "Removing background..."})

      result_path = await remove_bg_api_call(image_path, output_webp=True)

      writer.write({"agent": "background", "status": "complete", "path": result_path})
      return result_path

  @task
  async def optimization_agent(image_path: str, analysis: dict, writer: StreamWriter) -> str:
      """⚡ Applies custom optimizations based on analysis"""
      writer.write({"agent": "optimization", "status": "processing", "message": "Applying custom enhancements..."})

      magick_commands = generate_custom_commands(analysis)
      result_path = await apply_imagemagick_optimizations(image_path, magick_commands)

      writer.write({"agent": "optimization", "status": "complete", "commands": magick_commands})
      return result_path

  @task
  async def qc_agent(image_path: str, original_analysis: dict, writer: StreamWriter) -> dict:
      """✅ Quality control validation and approval"""
      writer.write({"agent": "qc", "status": "validating", "message": "Checking quality standards..."})

      qc_result = await claude_quality_check(image_path, original_analysis)

      writer.write({"agent": "qc", "status": "complete", "passed": qc_result["passed"]})
      return qc_result

  checkpointer = InMemorySaver()

  @entrypoint(checkpointer=checkpointer)
  async def agentic_photo_processor(
      inputs: dict, 
      *, 
      previous: dict = None,
      writer: StreamWriter
  ) -> dict:
      """🤖 Complete 4-agent photo processing workflow"""

      image_path = inputs["image_path"]
      retry_count = (previous or {}).get("retry_count", 0)

      # Agent 1: Analysis
      analysis = await analysis_agent(image_path, writer)

      # Agent 2: Background Removal  
      bg_removed = await background_agent(image_path, analysis, writer)

      # Agent 3: Optimization
      optimized = await optimization_agent(bg_removed, analysis, writer)

      # Agent 4: Quality Control
      qc_result = await qc_agent(optimized, analysis, writer)

      if qc_result["passed"]:
          return entrypoint.final(
              value={"final_image": optimized, "qc_passed": True},
              save={
                  "analysis": analysis,
                  "final_path": optimized,
                  "qc_report": qc_result,
                  "retry_count": retry_count
              }
          )

      # QC Failed - retry with refinements
      if retry_count < 2:
          writer.write({"agent": "qc", "status": "retry", "attempt": retry_count + 1})
          refined_analysis = {**analysis, **qc_result.get("improvements", {})}

          return entrypoint.final(
              value=await agentic_photo_processor(
                  {"image_path": image_path, "analysis": refined_analysis},
                  writer=writer
              ),
              save={"retry_count": retry_count + 1}
          )

      # Max retries reached
      return entrypoint.final(
          value={"final_image": optimized, "qc_passed": False, "max_retries": True},
          save={"retry_count": retry_count, "final_attempt": optimized}
      )

  Phase 1 CLI Interface:

  # cli_agentic.py
  import asyncio
  from pathlib import Path

  async def main():
      parser = argparse.ArgumentParser(description="Agentic Photo Editor")
      parser.add_argument("input_dir", help="Directory with images")
      parser.add_argument("--output-dir", help="Output directory")
      args = parser.parse_args()

      # Process each image with the agentic workflow
      for image_path in Path(args.input_dir).glob("*.{jpg,jpeg,png,webp}"):
          print(f"\n🎯 Processing {image_path.name}")

          config = {"configurable": {"thread_id": str(image_path.stem)}}

          async for event in agentic_photo_processor.astream_events(
              {"image_path": str(image_path)},
              config=config
          ):
              # Real-time streaming updates
              if event.get("agent"):
                  print(f"  {event['agent']}: {event['message']}")

          result = await agentic_photo_processor.ainvoke(
              {"image_path": str(image_path)},
              config=config
          )

          print(f"  ✅ Complete: {result['final_image']}")

  if __name__ == "__main__":
      asyncio.run(main())

  Phase 2: Web Interface on Top

  Once the CLI agentic workflow is solid, we layer on FastAPI + React:

  # web_server.py  
  from fastapi import FastAPI, WebSocket
  from fastapi.staticfiles import StaticFiles

  app = FastAPI()
  app.mount("/static", StaticFiles(directory="web"), name="static")

  @app.websocket("/ws/{session_id}")
  async def websocket_endpoint(websocket: WebSocket, session_id: str):
      await websocket.accept()

      # Same agentic workflow, streaming via WebSocket
      async for event in agentic_photo_processor.astream_events(request_data):
          await websocket.send_json({
              "agent": event.get("agent"),
              "status": event.get("status"),
              "message": event.get("message"),
              "session_id": session_id
          })

  Benefits of This Approach:

  1. ✅ Solid Foundation: CLI ensures the agentic logic works perfectly
  2. 🔄 Easy Testing: Test each agent independently via CLI
  3. 📊 Real-time Streaming: LangGraph streaming works identically in CLI and web
  4. 🎯 Modular: Each agent is a focused @task function
  5. 💾 State Management: Built-in checkpointing and retry logic
  6. 🌐 Web Ready: Same backend powers both CLI and web interfaces
