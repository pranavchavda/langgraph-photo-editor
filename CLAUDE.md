# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered agentic photo editor that combines Claude Sonnet 4 vision analysis with Gemini 2.5 Flash AI image editing to optimize product photography for e-commerce. The system uses LangGraph for multi-agent workflow orchestration.

## Architecture

**Multi-Agent LangGraph Workflow:**
- **Enhanced Analysis Agent** (Claude Sonnet 4) - Determines optimal processing strategy
- **Gemini Edit Agent** (Gemini 2.5 Flash) - Performs AI image editing with natural language
- **Background Agent** (remove.bg API) - Professional background removal  
- **ImageMagick Agent** - Parameter-based optimizations as fallback
- **QC Agent** (Claude) - Quality validation and retry logic

**Core Technologies:**
- LangGraph with functional API (`@task` decorators, `@entrypoint` orchestrator)
- Claude Sonnet 4 for vision analysis and quality control
- Gemini 2.5 Flash for AI-powered image editing
- ImageMagick for traditional photo optimization
- Rich terminal UI for progress tracking

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Main entry point - interactive chat mode
python photo_editor.py chat

# Process single image
python photo_editor.py process image.jpg --instructions "enhance chrome and make more vibrant"

# Batch processing
python photo_editor.py batch ./input-dir/ --output-dir ./output-dir/ --max-concurrent 3

# Configuration test
python photo_editor.py test
```

### Testing and Development
```bash
# Run enhanced workflow tests
python test_enhanced.py

# Debug specific components
python debug_analysis.py    # Test analysis agent
python debug_strategy.py    # Test strategy selection
python debug_workflow.py    # Test full workflow

# Other test files
python test_chat_gemini.py  # Test Gemini integration
python test_trim.py         # Test image processing utilities
```

## Code Structure

**Main Application Files:**
- `photo_editor.py` - Main entry point, delegates to enhanced CLI
- `src/cli_enhanced.py` - Enhanced CLI with Gemini 2.5 Flash support
- `src/workflow_enhanced.py` - 5-agent LangGraph workflow orchestration
- `src/agents_enhanced.py` - Enhanced agent implementations

**Legacy Components:**
- `src/cli.py` - Original CLI implementation
- `src/workflow.py` - Original 4-agent workflow
- `src/agents.py` - Original agent implementations

**Key Architectural Patterns:**
- All agents use async/await with proper error handling
- State management through LangGraph TypedDict schemas
- Progress tracking via StreamWriter for real-time updates
- Quality-based retry logic with parameter refinement
- Concurrent batch processing with configurable limits

## Environment Variables (Required)

```bash
# Core AI APIs
ANTHROPIC_API_KEY=your_claude_key_here        # Claude Sonnet 4
GEMINI_API_KEY=your_gemini_key_here           # Gemini 2.5 Flash

# Optional services
REMOVE_BG_API_KEY=your_removebg_key_here      # Background removal

# Processing settings (optional)
MAX_CONCURRENT_IMAGES=3                        # Batch concurrency
RETRY_ATTEMPTS=2                              # QC retry attempts
QUALITY_THRESHOLD=0.8                         # Minimum QC score
```

## File I/O Patterns

**Input Formats:** JPG, JPEG, PNG, WebP
**Output Format:** Always WebP (preserves transparency from background removal)

**Directory Structure:**
- Input images can be single files or directories
- Output preserves original filenames with quality indicators
- Failed QC results get quality suffix (e.g. `-q6.webp`, `-qfail.webp`)
- Intermediate files are cleaned up automatically

## Development Notes

**LangGraph Functional API Usage:**
- Use `@task` decorators for individual agents
- Use `@entrypoint` for workflow orchestration with checkpointing
- StreamWriter provides real-time progress updates to CLI
- InMemorySaver handles state persistence across retries

**Agent Communication:**
- Agents communicate through structured state objects
- Each agent updates specific state fields and logs progress
- QC agent provides feedback for retry parameter refinement
- Error handling with custom AgentError exceptions

**Testing Strategy:**
- Use test files in root directory for component testing
- Test images should be placed in `/tmp/` for consistency
- Each agent can be tested independently via debug scripts
- Full workflow testing through `test_enhanced.py`

## Dependencies

**System Requirements:**
- ImageMagick (must be installed and accessible via command line)
- Python 3.9+

**Key Python Packages:**
- `langgraph>=0.2.0` - Multi-agent workflow orchestration
- `langchain-anthropic>=0.2.0` - Claude integration
- `anthropic>=0.34.0` - Direct Claude API access
- `google-generativeai>=0.8.0` - Gemini 2.5 Flash image editing
- `click>=8.0.0` - CLI framework
- `rich>=13.0.0` - Terminal UI and progress display
- `pillow>=10.0.0` - Image format handling

## Development Notes for Claude Code
- Use specialized Claude Code subagents for further coding. there are several available 
