"""
Agentic Photo Editor - CLI Interface
Rich streaming progress display for the LangGraph workflow
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from dotenv import load_dotenv

from .workflow import agentic_photo_processor, process_image_batch


console = Console()


class AgenticProgressTracker:
    """Real-time progress tracking for the agentic workflow"""
    
    def __init__(self):
        self.current_image = ""
        self.agent_status = {}
        self.workflow_status = "starting"
        self.quality_score = 0
        self.retry_count = 0
        self.errors = []
        
    def update_from_event(self, event: Dict[str, Any]):
        """Update progress from streaming event"""
        
        # Workflow-level events
        if "workflow" in event:
            self.workflow_status = event["workflow"]
            if "retry_count" in event:
                self.retry_count = event["retry_count"]
                
        # Agent-level events  
        elif "agent" in event:
            agent = event["agent"]
            self.agent_status[agent] = {
                "status": event.get("status", "unknown"),
                "message": event.get("message", ""),
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Track quality score from QC agent
            if agent == "qc" and "quality_score" in event:
                self.quality_score = event["quality_score"]
                
        # Error tracking
        if event.get("status") == "error" or "error" in event:
            self.errors.append(event.get("error", event.get("message", "Unknown error")))
    
    def create_display(self) -> Layout:
        """Create rich layout for progress display"""
        layout = Layout()
        
        # Header with current image
        header = Panel(
            f"🤖 Agentic Photo Editor - Processing: {Path(self.current_image).name}",
            style="bold blue"
        )
        
        # Agent status table
        agent_table = Table(title="Agent Status", show_header=True)
        agent_table.add_column("Agent", style="cyan", width=12)
        agent_table.add_column("Status", width=15)
        agent_table.add_column("Message", style="dim")
        
        agents = ["analysis", "background", "optimization", "qc"]
        for agent in agents:
            status_info = self.agent_status.get(agent, {"status": "pending", "message": "Waiting..."})
            status = status_info["status"]
            message = status_info["message"]
            
            # Style status based on state
            if status == "complete" or status == "passed":
                status_display = Text("✅ Complete", style="green")
            elif status == "processing" or status == "analyzing" or status == "validating":
                status_display = Text("🔄 Working", style="yellow")
            elif status == "error" or status == "failed":
                status_display = Text("❌ Failed", style="red")
            elif status == "skipped":
                status_display = Text("⏭️  Skipped", style="dim")
            else:
                status_display = Text("⏳ Pending", style="dim")
                
            agent_table.add_row(f"🔍🎨⚡✅"[agents.index(agent)] + f" {agent.title()}", status_display, message)
        
        # Workflow info panel
        workflow_info = []
        workflow_info.append(f"Status: {self.workflow_status.title()}")
        if self.retry_count > 0:
            workflow_info.append(f"Retry Attempts: {self.retry_count}/2")
        if self.quality_score > 0:
            workflow_info.append(f"Quality Score: {self.quality_score:.1f}/10")
        if self.errors:
            workflow_info.append(f"Errors: {len(self.errors)}")
            
        workflow_panel = Panel(
            "\n".join(workflow_info),
            title="Workflow Info",
            style="blue"
        )
        
        # Layout structure
        layout.split_column(
            Layout(header, size=3),
            Layout(agent_table),
            Layout(workflow_panel, size=6)
        )
        
        return layout


async def process_single_image_with_progress(image_path: str) -> Dict[str, Any]:
    """Process a single image with live progress display"""
    
    tracker = AgenticProgressTracker()
    tracker.current_image = image_path
    
    console.print(f"\n🎯 Starting agentic processing for: {Path(image_path).name}")
    
    config = {"configurable": {"thread_id": str(Path(image_path).stem)}}
    
    with Live(tracker.create_display(), refresh_per_second=2, console=console) as live:
        try:
            # Stream the workflow execution with custom mode to capture agent events
            result = None
            async for chunk in agentic_photo_processor.astream(
                {"image_path": image_path},
                config=config,
                stream_mode="custom"
            ):
                # Update tracker with the custom streaming event from agents
                tracker.update_from_event(chunk)
                live.update(tracker.create_display())
                
                # Small delay for visual effect
                await asyncio.sleep(0.1)
            
            # Get the final result separately since custom mode doesn't return the final value
            result = await agentic_photo_processor.ainvoke(
                {"image_path": image_path},
                config=config
            )
            
            # Final status update
            if result.get("qc_passed", False):
                console.print(f"\n✅ Processing complete! Quality score: {result.get('quality_score', 0)}/10")
                console.print(f"📁 Final image: {result['final_image']}")
            elif result.get("max_retries", False):
                console.print(f"\n⚠️  Max retries reached. Best attempt saved.")
                console.print(f"📁 Final image: {result['final_image']}")
                console.print(f"❗ Issues found: {', '.join(result.get('issues', []))}")
            else:
                console.print(f"\n❌ Processing failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            console.print(f"\n💥 Critical error: {str(e)}")
            return {"error": str(e), "failed": True}


@click.group()
@click.version_option(version="0.1.0", message="Agentic Photo Editor v%(version)s")
def cli():
    """🤖 AI-powered agentic photo editor using Claude vision and LangGraph"""
    # Load environment variables
    load_dotenv()
    
    # Check required API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print("❌ ANTHROPIC_API_KEY environment variable not set", style="red")
        sys.exit(1)
    
    if not os.getenv("REMOVE_BG_API_KEY"):
        console.print("⚠️  REMOVE_BG_API_KEY not set - background removal will be skipped", style="yellow")


@cli.command()
@click.argument("image_path", type=click.Path(exists=True))
@click.option("--output-dir", type=click.Path(), help="Output directory for processed image")
def process(image_path: str, output_dir: str):
    """Process a single image with the agentic workflow"""
    
    image_path = Path(image_path).resolve()
    
    if not image_path.is_file():
        console.print(f"❌ Not a file: {image_path}", style="red")
        sys.exit(1)
    
    # Check if it's an image
    if image_path.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.webp']:
        console.print(f"❌ Not a supported image format: {image_path.suffix}", style="red")
        sys.exit(1)
    
    # Create output directory if specified
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Process the image
    result = asyncio.run(process_single_image_with_progress(str(image_path)))
    
    if result.get("failed"):
        sys.exit(1)


@cli.command()
@click.argument("input_dir", type=click.Path(exists=True))
@click.option("--output-dir", type=click.Path(), help="Output directory")
@click.option("--max-concurrent", default=3, help="Max concurrent image processing")
@click.option("--pattern", default="*.{jpg,jpeg,png,webp}", help="File pattern to match")
def batch(input_dir: str, output_dir: str, max_concurrent: int, pattern: str):
    """Process all images in a directory with the agentic workflow"""
    
    input_path = Path(input_dir).resolve()
    
    # Find all matching images
    image_files = []
    for ext in ['jpg', 'jpeg', 'png', 'webp']:
        image_files.extend(list(input_path.glob(f"*.{ext}")))
        image_files.extend(list(input_path.glob(f"*.{ext.upper()}")))
    
    if not image_files:
        console.print(f"❌ No supported images found in: {input_path}", style="red")
        sys.exit(1)
    
    console.print(f"📁 Found {len(image_files)} images to process")
    
    # Create output directory
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Process batch
    console.print(f"\n🚀 Starting batch processing with {max_concurrent} concurrent workers...")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        batch_task = progress.add_task("Processing batch...", total=len(image_files))
        
        async def run_batch():
            image_paths = [str(img) for img in image_files]
            results = await process_image_batch(
                image_paths, 
                output_dir=output_dir,
                max_concurrent=max_concurrent
            )
            
            # Update progress as results come in  
            progress.update(batch_task, completed=results["total_processed"])
            
            return results
        
        results = asyncio.run(run_batch())
    
    # Display results summary
    summary_table = Table(title="Batch Processing Results")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Count", style="green")
    
    summary_table.add_row("Total Images", str(results["total_processed"]))
    summary_table.add_row("Successful", str(results["successful"]))
    summary_table.add_row("Failed", str(results["failed"]))
    summary_table.add_row("Success Rate", f"{results['summary']['success_rate']:.1f}%")
    
    console.print("\n")
    console.print(summary_table)
    
    if results["failed"] > 0:
        console.print(f"\n⚠️  {results['failed']} images failed processing. Check logs above for details.", style="yellow")


@cli.command()
def chat():
    """Interactive chat mode for natural language photo processing instructions"""
    
    console.print("🤖 [bold blue]Agentic Photo Editor - Interactive Chat Mode[/bold blue]")
    console.print("Give me natural language instructions for photo processing!\n")
    
    console.print("[dim]Examples:[/dim]")
    console.print("[dim]  • Process /path/to/images/ with brighter colors and sharper details[/dim]")
    console.print("[dim]  • Make the coffee machines in ./luce-images/ more vibrant[/dim]")
    console.print("[dim]  • Process image.jpg but keep it more natural, less saturated[/dim]")
    console.print("[dim]  • Apply chrome optimization to all steel machines in folder/[/dim]")
    console.print("[dim]  • Type 'quit' to exit[/dim]\n")
    
    asyncio.run(interactive_chat_session())


async def interactive_chat_session():
    """Main interactive chat loop"""
    from rich.prompt import Prompt
    
    while True:
        try:
            # Get user instruction
            user_input = Prompt.ask("\n[bold green]Your instruction[/bold green]")
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                console.print("👋 Goodbye!", style="blue")
                break
                
            # Parse the instruction
            parsed_instruction = await parse_chat_instruction(user_input)
            
            if not parsed_instruction:
                console.print("❌ I couldn't understand that instruction. Please try again.", style="red")
                continue
                
            # Show what was understood
            console.print(f"\n🎯 [bold]Understood:[/bold]")
            console.print(f"   📁 Target: {parsed_instruction['target']}")
            console.print(f"   📝 Instructions: {parsed_instruction['instructions']}")
            console.print(f"   ⚙️  Processing mode: {parsed_instruction['mode']}")
            
            # Confirm before processing
            if not Prompt.ask("\nProceed with processing?", choices=["y", "n"], default="y") == "y":
                continue
                
            # Execute the processing
            await execute_chat_instruction(parsed_instruction)
            
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!", style="blue")
            break
        except Exception as e:
            console.print(f"\n❌ Error: {e}", style="red")


async def parse_chat_instruction(user_input: str) -> Optional[Dict[str, Any]]:
    """Parse natural language instruction using Claude"""
    
    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        parsing_prompt = f"""
        Parse this photo processing instruction into structured data.
        
        User instruction: "{user_input}"
        
        Extract and return JSON with:
        - target: file path or directory path mentioned (or null if none)
        - instructions: specific processing requirements/style preferences 
        - mode: "single" for one file, "batch" for directory/multiple files
        - adjustments: {{
            brightness_preference: number (-50 to +50, 0=no preference),
            contrast_preference: number (-50 to +50, 0=no preference),
            saturation_preference: number (-50 to +50, 0=no preference), 
            style_notes: [array of specific style requirements]
          }}
        
        Examples:
        "Process /path/images/ brighter" -> {{"target": "/path/images/", "mode": "batch", "instructions": "make images brighter", "adjustments": {{"brightness_preference": 20, "contrast_preference": 0, "saturation_preference": 0, "style_notes": ["brighter", "enhanced brightness"]}}}}
        
        "Make image.jpg more natural" -> {{"target": "image.jpg", "mode": "single", "instructions": "keep natural appearance", "adjustments": {{"brightness_preference": 0, "contrast_preference": 0, "saturation_preference": -10, "style_notes": ["natural", "less processing"]}}}}
        
        Be specific about the target path and processing preferences.
        """
        
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": parsing_prompt}]
        )
        
        response_text = response.content[0].text
        
        # Extract JSON
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        elif "{" in response_text:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_text = response_text[json_start:json_end]
        else:
            return None
            
        return json.loads(json_text)
        
    except Exception as e:
        console.print(f"❌ Failed to parse instruction: {e}", style="red")
        return None


async def execute_chat_instruction(instruction: Dict[str, Any]):
    """Execute the parsed chat instruction"""
    
    target = instruction.get('target')
    mode = instruction.get('mode', 'single')
    custom_instructions = instruction.get('instructions', '')
    adjustments = instruction.get('adjustments', {})
    
    # Validate target path
    if target:
        target_path = Path(target).expanduser().resolve()
        if not target_path.exists():
            console.print(f"❌ Path not found: {target_path}", style="red")
            return
    else:
        console.print("❌ No target file or directory specified", style="red")
        return
    
    # Store custom instructions for the analysis agent
    os.environ["CUSTOM_PROCESSING_INSTRUCTIONS"] = custom_instructions
    if adjustments:
        os.environ["CUSTOM_ADJUSTMENTS"] = json.dumps(adjustments)
    
    try:
        if mode == "single" and target_path.is_file():
            # Process single file
            console.print(f"\n🚀 Processing single image with custom instructions...")
            result = await process_single_image_with_progress(str(target_path))
            
        elif mode == "batch" and target_path.is_dir():
            # Process directory
            image_files = []
            for ext in ['jpg', 'jpeg', 'png', 'webp']:
                image_files.extend(list(target_path.glob(f"*.{ext}")))
                image_files.extend(list(target_path.glob(f"*.{ext.upper()}")))
            
            if not image_files:
                console.print(f"❌ No supported images found in: {target_path}", style="red")
                return
                
            console.print(f"\n🚀 Processing {len(image_files)} images with custom instructions...")
            
            # Use the existing batch processing logic but with custom instructions
            from .workflow import process_image_batch
            results = await process_image_batch(
                [str(img) for img in image_files[:5]],  # Limit to 5 for demo
                max_concurrent=2
            )
            
            # Display results
            console.print(f"\n📊 [bold]Batch Results:[/bold]")
            console.print(f"   ✅ Successful: {results['successful']}")
            console.print(f"   ❌ Failed: {results['failed']}")
            console.print(f"   📈 Success Rate: {results['summary']['success_rate']:.1f}%")
            
        else:
            console.print("❌ Invalid target or mode combination", style="red")
            
    finally:
        # Clean up environment variables
        os.environ.pop("CUSTOM_PROCESSING_INSTRUCTIONS", None)
        os.environ.pop("CUSTOM_ADJUSTMENTS", None)


@cli.command()
def test():
    """Test the agentic workflow with sample processing"""
    
    console.print("🧪 Testing agentic photo editor configuration...")
    
    # Check API keys
    anthropic_key = os.getenv("ANTHROPIC_API_KEY") 
    removebg_key = os.getenv("REMOVE_BG_API_KEY")
    
    status_table = Table(title="Configuration Status")
    status_table.add_column("Component", style="cyan")
    status_table.add_column("Status", style="green")
    
    status_table.add_row("Anthropic API", "✅ Ready" if anthropic_key else "❌ Missing")
    status_table.add_row("Remove.bg API", "✅ Ready" if removebg_key else "⚠️  Missing (optional)")
    status_table.add_row("ImageMagick", "✅ Available" if os.system("which magick > /dev/null 2>&1") == 0 else "❌ Not found")
    
    console.print(status_table)
    
    if not anthropic_key:
        console.print("\n❌ Please set ANTHROPIC_API_KEY environment variable", style="red")
        sys.exit(1)
    
    console.print("\n✅ Configuration looks good! Ready to process images.", style="green")


def main():
    """Main CLI entry point"""
    cli()


if __name__ == "__main__":
    main()