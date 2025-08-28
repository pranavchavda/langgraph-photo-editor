"""
Enhanced Agentic Photo Editor - CLI with Gemini 2.5 Flash Image Support
Supports both original and enhanced workflows
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from contextlib import nullcontext

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from dotenv import load_dotenv

# Import enhanced workflow system
from .workflow_enhanced import (
    enhanced_agentic_processor, 
    process_single_image_enhanced,
    process_image_batch_enhanced
)

# Import classic workflow functions when needed
def import_classic_functions():
    from .cli import process_single_image_with_progress
    from .workflow import process_image_batch
    return process_single_image_with_progress, process_image_batch

console = Console()


class EnhancedProgressTracker:
    """Enhanced progress tracker for the 5-agent workflow"""
    
    def __init__(self, json_output=False):
        self.json_output = json_output
        self.current_stage = "initializing"
        self.agent_status = {
            "analysis": "pending",
            "background": "pending", 
            "gemini": "pending",
            "imagemagick": "pending",
            "qc": "pending"
        }
        self.quality_score = None
        self.editing_strategy = None
        self.messages = []
        self.errors = []
    
    def update(self, event: Dict[str, Any]):
        """Update tracker with workflow events"""
        
        # Handle different event types from LangGraph streaming
        if isinstance(event, dict):
            # Direct event from workflow writer
            if "stage" in event:
                stage = event["stage"]
                
                # Map stages to agents and update status
                stage_agent_map = {
                    "analysis": ("analysis", "running"),
                    "analysis_complete": ("analysis", "completed"),
                    "background_removal": ("background", "running"),
                    "gemini_editing": ("gemini", "running"),
                    "gemini_complete": ("gemini", "completed"), 
                    "gemini_failed": ("gemini", "error"),
                    "imagemagick_optimization": ("imagemagick", "running"),
                    "quality_control": ("qc", "running"),
                    "imagemagick_fallback": ("imagemagick", "running"),
                    "enhanced_success": ("qc", "completed"),
                    "enhanced_complete_imperfect": ("qc", "completed"),
                    "enhanced_error": ("qc", "error")
                }
                
                if stage in stage_agent_map:
                    agent, status = stage_agent_map[stage]
                    self.agent_status[agent] = status
                
                self.current_stage = stage
                
                # Output JSON progress for Electron
                if self.json_output:
                    self._output_json_progress()
            
            # Handle workflow events
            if "workflow" in event:
                workflow_type = event["workflow"]
                if workflow_type == "enhanced_started":
                    self.current_stage = "starting"
                    # Set all agents to pending initially
                    for agent in self.agent_status:
                        self.agent_status[agent] = "pending"
            
            # Handle strategy updates
            if "strategy" in event:
                self.editing_strategy = event["strategy"]
                
            # Handle quality updates  
            if "quality_score" in event:
                self.quality_score = event["quality_score"]
            
            # Add messages
            if "message" in event:
                self.messages.append(event["message"])
                
            # Handle errors
            if "error" in event:
                self.errors.append(event["error"])
    
    def _output_json_progress(self):
        """Output JSON progress data for Electron integration"""
        if self.json_output:
            progress_data = {
                "stage": self.current_stage,
                "message": self.messages[-1] if self.messages else "Processing...",
                "agentStatus": self.agent_status,
                "quality_score": self.quality_score,
                "strategy": self.editing_strategy
            }
            print(json.dumps(progress_data), flush=True)
    
    def render(self) -> Panel:
        """Render current progress as Rich panel"""
        
        # Create status table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Agent", style="cyan", no_wrap=True)
        table.add_column("Status", no_wrap=True) 
        table.add_column("Details", style="dim")
        
        # Agent status with emojis
        status_emojis = {
            "pending": "⏸️",
            "analyzing": "🔍",
            "removing": "🖼️",
            "editing": "🎨", 
            "optimizing": "⚡",
            "evaluating": "✅",
            "complete": "✅",
            "error": "❌",
            "skipped": "⏭️"
        }
        
        agent_names = {
            "analysis": "Analysis (Claude)",
            "background": "Background Removal", 
            "gemini": "Gemini 2.5 Flash",
            "imagemagick": "ImageMagick",
            "qc": "Quality Control"
        }
        
        for agent, status in self.agent_status.items():
            emoji = status_emojis.get(status, "⏸️")
            style = "green" if status == "complete" else "red" if status == "error" else "yellow"
            table.add_row(
                agent_names[agent],
                f"{emoji} {status.title()}",
                "",
                style=style
            )
        
        # Add strategy and quality info
        if self.editing_strategy:
            table.add_row("", "", f"Strategy: {self.editing_strategy}", style="blue")
        if self.quality_score is not None:
            score_style = "green" if self.quality_score >= 9 else "yellow" if self.quality_score >= 7 else "red"
            table.add_row("", "", f"Quality: {self.quality_score}/10", style=score_style)
        
        # Recent messages
        recent_messages = "\n".join(self.messages[-3:]) if self.messages else "Initializing..."
        
        # Create panel with table as main content
        title = f"🤖 Enhanced Agentic Photo Editor - {self.current_stage.replace('_', ' ').title()}"
        
        # Combine table with messages
        from rich.console import Group
        from rich.text import Text
        
        content_items = [table]
        
        # Add recent messages
        if self.messages:
            content_items.append(Text("\n💬 Recent Updates:", style="bold"))
            content_items.append(Text(recent_messages))
        
        # Add errors if any
        if self.errors:
            content_items.append(Text("\n❌ Errors:", style="bold red"))
            content_items.append(Text("\n".join(self.errors[-2:]), style="red"))
        
        return Panel(
            Group(*content_items),
            title=title,
            border_style="blue",
            padding=(1, 2)
        )


async def process_single_with_enhanced_progress(
    image_path: str, 
    use_enhanced: bool = True, 
    custom_instructions: Optional[str] = None,
    output_dir: Optional[str] = None,
    json_output: bool = False
) -> Dict[str, Any]:
    """Process single image with enhanced progress display"""
    
    tracker = EnhancedProgressTracker(json_output=json_output)
    
    if json_output:
        # In JSON mode, don't use Live rendering
        live_context = None
    else:
        # Use Live rendering for console output
        live_context = Live(tracker.render(), refresh_per_second=2)
    
    with live_context if live_context else nullcontext() as live:
        # Set up streaming callback
        def update_callback(event):
            tracker.update(event)
            if not json_output and live:
                live.update(tracker.render())
        
        try:
            if use_enhanced:
                # Import enhanced workflow functions
                from .workflow_enhanced import enhanced_agentic_processor
                import uuid
                
                # Set up custom instructions in environment if provided
                if custom_instructions:
                    os.environ["CUSTOM_PROCESSING_INSTRUCTIONS"] = custom_instructions
                
                # Process with enhanced workflow and streaming
                config = {"configurable": {"thread_id": str(uuid.uuid4())}}
                
                # Use streaming to capture real-time progress and get result
                result = None
                async for chunk in enhanced_agentic_processor.astream({
                    "image_path": image_path,
                    "custom_instructions": custom_instructions
                }, config=config):
                    # Handle streaming events from the workflow
                    if isinstance(chunk, dict):
                        if 'workflow' in chunk or 'stage' in chunk:
                            update_callback(chunk)
                        # The final result will be in the last chunk
                        if 'final_image' in chunk or 'final_image_path' in chunk:
                            result = chunk
                
                # If we didn't get the result from streaming, get it directly
                if not result:
                    result = await enhanced_agentic_processor.ainvoke({
                        "image_path": image_path,
                        "custom_instructions": custom_instructions
                    }, config=config)
                
                # Handle output directory
                if output_dir and result.get("final_image"):
                    output_path = Path(output_dir) / Path(result["final_image"]).name
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    import shutil
                    shutil.move(result["final_image"], str(output_path))
                    result["final_image"] = str(output_path)
            else:
                # Use original workflow
                result = await process_single_image_with_progress(image_path)
            
            # Final update
            if result.get("qc_passed", False):
                tracker.messages.append(f"✅ Processing complete! Quality: {result.get('quality_score', 0)}/10")
                tracker.quality_score = result.get('quality_score', 0)
            else:
                tracker.messages.append(f"⚠️ Processing completed with issues")
                tracker.quality_score = result.get('quality_score', 0)
            
            # Final JSON output for Electron
            if json_output:
                tracker._output_json_progress()
            
            if live and not json_output:
                live.update(tracker.render())
            
            return result
            
        except Exception as e:
            tracker.errors.append(str(e))
            live.update(tracker.render())
            raise


@click.group()
@click.option('--enhanced/--classic', default=True, help='Use enhanced Gemini 2.5 Flash workflow (default) or classic workflow')
@click.pass_context
def cli(ctx, enhanced):
    """🤖 Agentic Photo Editor with Gemini 2.5 Flash Image Support"""
    load_dotenv()
    
    # Store enhanced flag in context
    ctx.ensure_object(dict)
    ctx.obj['enhanced'] = enhanced
    
    # Check required API keys
    required_keys = ["ANTHROPIC_API_KEY"]
    if enhanced:
        required_keys.append("GEMINI_API_KEY")
    
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        console.print(f"❌ Missing required API keys: {', '.join(missing_keys)}", style="red")
        console.print("\n📝 Set up your API keys in .env file:", style="yellow")
        for key in missing_keys:
            console.print(f"   {key}=your_key_here")
        sys.exit(1)
    
    # Show workflow mode
    mode = "Enhanced (Gemini 2.5 Flash)" if enhanced else "Classic (ImageMagick only)"
    console.print(f"🚀 Using {mode} workflow", style="blue")


@cli.command()
@click.argument('image_path', type=click.Path(exists=True))
@click.option('--output-dir', type=click.Path(), help='Output directory for processed image')
@click.option('--instructions', help='Custom processing instructions')
@click.option('--json-output', is_flag=True, help='Output JSON progress for Electron integration')
@click.pass_context
async def process(ctx, image_path, output_dir, instructions, json_output):
    """Process a single image"""
    
    use_enhanced = ctx.obj['enhanced']
    
    if not json_output:
        console.print(f"🖼️ Processing: {Path(image_path).name}")
        if instructions:
            console.print(f"📝 Instructions: {instructions}")
    
    try:
        if use_enhanced:
            result = await process_single_with_enhanced_progress(
                image_path, 
                use_enhanced=True,
                custom_instructions=instructions,
                output_dir=output_dir,
                json_output=json_output
            )
        else:
            # Import classic function
            process_single_image_with_progress, _ = import_classic_functions()
            result = await process_single_image_with_progress(image_path)
            
            # Handle output dir for classic workflow
            if output_dir and result.get("final_image"):
                output_path = Path(output_dir) / Path(result["final_image"]).name
                output_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.move(result["final_image"], str(output_path))
                result["final_image"] = str(output_path)
        
        # Show results (only in non-JSON mode)
        if not json_output:
            if result.get("qc_passed", False):
                console.print(f"✅ Processing successful!", style="green")
                console.print(f"📊 Quality score: {result.get('quality_score', 0)}/10")
                if use_enhanced:
                    console.print(f"🎯 Strategy used: {result.get('editing_strategy', 'unknown')}")
                    if result.get('gemini_used'):
                        console.print("🎨 Gemini 2.5 Flash editing applied")
                    if result.get('imagemagick_used'):
                        console.print("⚡ ImageMagick optimization applied")
            else:
                console.print(f"⚠️ Processing completed with quality issues", style="yellow")
                console.print(f"📊 Quality score: {result.get('quality_score', 0)}/10")
            
            if result.get("final_image"):
                console.print(f"💾 Output: {result['final_image']}")
        else:
            # JSON output final status for Electron
            final_status = {
                "stage": "completed" if result.get("qc_passed") else "completed_with_issues",
                "message": f"Processing complete! Quality: {result.get('quality_score', 0)}/10",
                "agentStatus": {
                    "analysis": "completed",
                    "background": "completed",
                    "gemini": "completed",
                    "imagemagick": "completed",
                    "qc": "completed"
                },
                "strategy": result.get('editing_strategy'),
                "quality_score": result.get('quality_score', 0),
                "output_path": result.get('final_image'),
                "success": result.get("qc_passed", False)
            }
            print(json.dumps(final_status), flush=True)
        
    except Exception as e:
        if not json_output:
            console.print(f"❌ Processing failed: {e}", style="red")
        else:
            # JSON error output
            error_status = {
                "stage": "error",
                "message": f"Processing failed: {str(e)}",
                "agentStatus": {
                    "analysis": "error",
                    "background": "error",
                    "gemini": "error",
                    "imagemagick": "error",
                    "qc": "error"
                },
                "success": False,
                "error": str(e)
            }
            print(json.dumps(error_status), flush=True)
        sys.exit(1)


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True))
@click.option('--output-dir', type=click.Path(), help='Output directory')
@click.option('--max-concurrent', default=3, help='Maximum concurrent processing')
@click.option('--instructions', help='Custom processing instructions')
@click.option('--pattern', default='*.{jpg,jpeg,png,webp}', help='File pattern to match')
@click.pass_context
async def batch(ctx, input_dir, output_dir, max_concurrent, instructions, pattern):
    """Process a directory of images"""
    
    use_enhanced = ctx.obj['enhanced']
    
    console.print(f"📁 Processing directory: {input_dir}")
    console.print(f"⚡ Concurrency: {max_concurrent}")
    if instructions:
        console.print(f"📝 Instructions: {instructions}")
    
    try:
        if use_enhanced:
            result = await process_image_batch_enhanced(
                input_dir,
                output_dir,
                max_concurrent,
                instructions,
                pattern
            )
        else:
            # Import classic function
            _, process_image_batch = import_classic_functions()
            result = await process_image_batch(
                input_dir,
                output_dir, 
                max_concurrent,
                pattern
            )
        
        # Show batch results
        total = result['total_images']
        successful = result['successful']
        failed = result['failed']
        success_rate = result['success_rate']
        
        console.print(f"\n📊 Batch Processing Results:")
        console.print(f"   Total images: {total}")
        console.print(f"   Successful: {successful}", style="green")
        console.print(f"   Failed: {failed}", style="red" if failed > 0 else "dim")
        console.print(f"   Success rate: {success_rate:.1%}")
        
    except Exception as e:
        console.print(f"❌ Batch processing failed: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.pass_context
async def chat(ctx):
    """Interactive chat mode with enhanced workflow support"""
    
    use_enhanced = ctx.obj['enhanced']
    mode = "Enhanced (Gemini 2.5 Flash)" if use_enhanced else "Classic (ImageMagick only)"
    
    console.print(Panel(
        f"🤖 Agentic Photo Editor - Interactive Chat Mode\n"
        f"Mode: {mode}\n\n"
        f"Give me natural language instructions for photo processing!\n\n"
        f"Examples:\n"
        f"  • Process /path/to/images/ with brighter colors and sharper details\n"
        f"  • Make the coffee machines in ./luce-images/ more vibrant\n"
        f"  • Process image.jpg but keep it more natural, less saturated\n"
        f"  • Apply chrome optimization to all steel machines in folder/\n"
        f"  • Type 'quit' to exit",
        title="🤖 Enhanced Chat Mode",
        border_style="green"
    ))
    
    while True:
        try:
            instruction = console.input("\n[bold blue]Your instruction:[/bold blue] ")
            
            if instruction.lower() in ['quit', 'exit', 'q']:
                console.print("👋 Goodbye!", style="green")
                break
            
            if not instruction.strip():
                console.print("Please provide an instruction.", style="yellow")
                continue
            
            # Parse instruction (simplified - you could enhance this)
            parsed = await parse_chat_instruction(instruction)
            
            if parsed:
                target = parsed.get('target')
                mode_type = parsed.get('mode', 'single')
                custom_instructions = parsed.get('instructions', '')
                
                # Show what was understood
                console.print(f"\n🎯 [bold]Understood:[/bold]")
                console.print(f"   📁 Target: {target}")
                console.print(f"   📝 Instructions: {custom_instructions}")
                console.print(f"   ⚙️  Processing mode: {mode_type}")
                console.print(f"   🤖 Workflow: {mode}")
                
                # Confirm before processing
                if console.input(f"\n[yellow]Proceed with processing? [y/n]:[/yellow] ").lower() == 'y':
                    await execute_enhanced_chat_instruction(parsed, use_enhanced)
                else:
                    console.print("Cancelled.", style="dim")
            else:
                console.print("❌ Could not understand instruction. Please try again.", style="red")
                
        except (KeyboardInterrupt, EOFError):
            console.print("\n👋 Goodbye!", style="green")
            break
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")


async def parse_chat_instruction(instruction: str) -> Optional[Dict[str, Any]]:
    """Parse natural language instruction using Claude"""
    
    try:
        # Use Claude to parse the instruction
        from anthropic import AsyncAnthropic
        
        client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        parsing_prompt = f"""
        Parse this photo processing instruction into structured data:
        "{instruction}"
        
        Extract:
        - target: file path or directory path (REQUIRED - the path mentioned in the instruction)
        - mode: Determine automatically:
          * "batch" if target appears to be a directory (no file extension, folder-like name)
          * "single" if target appears to be a specific image file (.jpg, .png, .webp, etc.)
          * Default to "batch" if uncertain
        - instructions: natural language processing instructions (everything after the path)
        
        IMPORTANT: A path like "/path/folder" or "test1" or "images" is usually a directory → use "batch"
        A path like "image.jpg" or "photo.webp" is usually a file → use "single"
        
        Return JSON only:
        {{
            "target": "exact/path/from/instruction",
            "mode": "batch",
            "instructions": "processing instructions"
        }}
        """
        
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
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


async def execute_enhanced_chat_instruction(instruction: Dict[str, Any], use_enhanced: bool):
    """Execute the parsed chat instruction with enhanced workflow"""
    
    target = instruction.get('target')
    mode_type = instruction.get('mode', 'single')
    custom_instructions = instruction.get('instructions', '')
    
    # Validate target path
    if target:
        target_path = Path(target).expanduser().resolve()
        if not target_path.exists():
            console.print(f"❌ Path not found: {target_path}", style="red")
            return
    else:
        console.print("❌ No target file or directory specified", style="red")
        return
    
    try:
        # Auto-correct mode based on actual file type
        if target_path.is_file() and mode_type == "batch":
            mode_type = "single"
            console.print("🔄 Auto-corrected to single file mode")
        elif target_path.is_dir() and mode_type == "single":
            mode_type = "batch"
            console.print("🔄 Auto-corrected to batch directory mode")
        
        if mode_type == "single" and target_path.is_file():
            # Process single file with enhanced workflow
            console.print(f"\n🚀 Processing single image with enhanced workflow...")
            
            if use_enhanced:
                # Use direct invoke to show the agent debug messages
                result = await process_single_image_enhanced(str(target_path), custom_instructions)
            else:
                # Set custom instructions in environment for classic workflow  
                if custom_instructions:
                    os.environ["CUSTOM_PROCESSING_INSTRUCTIONS"] = custom_instructions
                process_single_image_with_progress, _ = import_classic_functions()
                result = await process_single_image_with_progress(str(target_path))
                
        elif mode_type == "batch" and target_path.is_dir():
            # Process directory with enhanced workflow
            image_files = []
            for ext in ['jpg', 'jpeg', 'png', 'webp']:
                image_files.extend(list(target_path.glob(f"*.{ext}")))
                image_files.extend(list(target_path.glob(f"*.{ext.upper()}")))
            
            if not image_files:
                console.print(f"❌ No supported images found in: {target_path}", style="red")
                return
                
            console.print(f"\n🚀 Processing {len(image_files)} images with enhanced workflow...")
            
            if use_enhanced:
                result = await process_image_batch_enhanced(
                    str(target_path),
                    None,  # Same directory output
                    3,     # Default concurrency
                    custom_instructions
                )
            else:
                # Set custom instructions for classic workflow
                if custom_instructions:
                    os.environ["CUSTOM_PROCESSING_INSTRUCTIONS"] = custom_instructions
                _, process_image_batch = import_classic_functions()
                result = await process_image_batch(str(target_path))
        else:
            console.print(f"❌ Invalid target: Expected file for single mode or directory for batch mode", style="red")
            return
        
        # Show results
        if isinstance(result, dict):
            if "total_images" in result:
                # Batch results
                console.print(f"\n✅ Batch processing complete!")
                console.print(f"📊 Processed: {result['successful']}/{result['total_images']} images")
                console.print(f"📈 Success rate: {result['success_rate']:.1%}")
            else:
                # Single image results
                console.print(f"\n✅ Processing complete!")
                if result.get('qc_passed'):
                    console.print(f"📊 Quality: {result.get('quality_score', 0)}/10", style="green")
                    if use_enhanced:
                        console.print(f"🎯 Strategy: {result.get('editing_strategy', 'unknown')}")
                else:
                    console.print(f"⚠️ Quality issues detected", style="yellow")
        
    except Exception as e:
        console.print(f"❌ Processing failed: {e}", style="red")


@cli.command()
def test():
    """Test API key configuration and system readiness"""
    
    console.print("🔧 Testing system configuration...\n")
    
    # Test API keys
    api_tests = [
        ("Anthropic API", "ANTHROPIC_API_KEY"),
        ("Gemini API", "GEMINI_API_KEY"),
        ("remove.bg API", "REMOVE_BG_API_KEY")
    ]
    
    for name, key in api_tests:
        if os.getenv(key):
            console.print(f"✅ {name}: Configured", style="green")
        else:
            status = "Required" if key in ["ANTHROPIC_API_KEY", "GEMINI_API_KEY"] else "Optional"
            style = "red" if status == "Required" else "yellow"
            console.print(f"❌ {name}: Missing ({status})", style=style)
    
    # Test ImageMagick
    try:
        import subprocess
        result = subprocess.run(["magick", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            console.print(f"✅ ImageMagick: {version_line}", style="green")
        else:
            console.print("❌ ImageMagick: Not working", style="red")
    except FileNotFoundError:
        console.print("❌ ImageMagick: Not installed", style="red")
    
    # Test Python packages
    required_packages = [
        ("anthropic", "anthropic"),
        ("google-generativeai", "google.generativeai"), 
        ("langgraph", "langgraph"),
        ("requests", "requests"),
        ("rich", "rich"),
        ("click", "click"),
        ("pillow", "PIL")
    ]
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            console.print(f"✅ {package_name}: Installed", style="green")
        except ImportError:
            console.print(f"❌ {package_name}: Missing", style="red")
    
    console.print(f"\n🚀 System ready for enhanced photo editing!")


def main():
    """Main entry point"""
    # Convert async commands
    def make_async_command(coro):
        def wrapper(*args, **kwargs):
            return asyncio.run(coro(*args, **kwargs))
        return wrapper
    
    # Replace async commands
    cli.commands['process'].callback = make_async_command(cli.commands['process'].callback)
    cli.commands['batch'].callback = make_async_command(cli.commands['batch'].callback)
    cli.commands['chat'].callback = make_async_command(cli.commands['chat'].callback)
    
    cli()


if __name__ == "__main__":
    main()