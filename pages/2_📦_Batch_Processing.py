"""
Streamlit Batch Processing Interface for Doug's Photo Editor
Process multiple images at once!
"""

import streamlit as st
import asyncio
from pathlib import Path
import tempfile
import zipfile
from PIL import Image
import os
from datetime import datetime
import streamlit.components.v1 as components
from concurrent.futures import ThreadPoolExecutor
import io

# Import our existing workflow
from src.workflow_enhanced import process_single_image_enhanced

# Page config
st.set_page_config(
    page_title="Doug's Batch Photo Editor",
    page_icon="📸",
    layout="wide"
)

# Initialize session state
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = []
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'api_keys' not in st.session_state:
    st.session_state.api_keys = {
        'anthropic': '',
        'gemini': '',
        'removebg': ''
    }

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .batch-progress {
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# JavaScript for localStorage
components.html("""
<script>
(function() {
    // Get and save API keys from localStorage
    function getStoredKeys() {
        return {
            anthropic: localStorage.getItem('photoEditor_anthropic') || '',
            gemini: localStorage.getItem('photoEditor_gemini') || '',
            removebg: localStorage.getItem('photoEditor_removebg') || ''
        };
    }
    
    function saveKeys() {
        const inputs = document.querySelectorAll('input[type="password"]');
        if (inputs.length >= 1) {
            localStorage.setItem('photoEditor_anthropic', inputs[0].value || '');
        }
        if (inputs.length >= 2) {
            localStorage.setItem('photoEditor_gemini', inputs[1].value || '');
        }
        if (inputs.length >= 3) {
            localStorage.setItem('photoEditor_removebg', inputs[2].value || '');
        }
    }
    
    // Auto-populate on load
    window.addEventListener('load', function() {
        setTimeout(function() {
            const stored = getStoredKeys();
            const inputs = document.querySelectorAll('input[type="password"]');
            
            if (inputs.length >= 1 && stored.anthropic && !inputs[0].value) {
                inputs[0].value = stored.anthropic;
                inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
            }
            if (inputs.length >= 2 && stored.gemini && !inputs[1].value) {
                inputs[1].value = stored.gemini;
                inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
            }
            if (inputs.length >= 3 && stored.removebg && !inputs[2].value) {
                inputs[2].value = stored.removebg;
                inputs[2].dispatchEvent(new Event('input', { bubbles: true }));
            }
        }, 100);
    });
    
    // Save on change
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(function() {
            document.querySelectorAll('input[type="password"]').forEach(input => {
                input.addEventListener('change', saveKeys);
                input.addEventListener('blur', saveKeys);
            });
        }, 500);
    });
})();
</script>
""", height=0)

# Logo and title
col_logo, col_title = st.columns([1, 4])

with col_logo:
    logo_path = Path("logo.jpeg")
    if logo_path.exists():
        logo_image = Image.open(logo_path)
        st.image(logo_image, width=150)
    else:
        st.write("🤖")

with col_title:
    st.title("Doug's Batch Photo Editor")
    st.markdown("""
    Upload multiple product photos and process them all at once!
    Perfect for processing your entire product catalog.
    """)

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("API Keys")
    st.markdown("*Your API keys are stored locally in your browser*")
    
    anthropic_key = st.text_input(
        "Anthropic API Key", 
        type="password",
        key="anthropic_key_input",
        value=st.session_state.api_keys['anthropic'],
        help="Required for image analysis"
    )
    
    gemini_key = st.text_input(
        "Gemini API Key", 
        type="password",
        key="gemini_key_input",
        value=st.session_state.api_keys['gemini'],
        help="Required for AI editing"
    )
    
    removebg_key = st.text_input(
        "Remove.bg API Key (Optional)", 
        type="password",
        key="removebg_key_input",
        value=st.session_state.api_keys['removebg'],
        help="Optional for background removal"
    )
    
    # Update session state
    if anthropic_key != st.session_state.api_keys['anthropic']:
        st.session_state.api_keys['anthropic'] = anthropic_key
    if gemini_key != st.session_state.api_keys['gemini']:
        st.session_state.api_keys['gemini'] = gemini_key
    if removebg_key != st.session_state.api_keys['removebg']:
        st.session_state.api_keys['removebg'] = removebg_key
    
    st.subheader("Processing Options")
    use_gemini = st.checkbox("Use Gemini 2.5 Flash", value=True)
    remove_background = st.checkbox("Remove Background", value=False)
    max_concurrent = st.slider("Concurrent Processing", 1, 5, 2, 
                              help="Process multiple images at once (faster but uses more resources)")
    
    st.info("💡 Tip: Start with 2 concurrent for best balance")
    
    with st.expander("🔑 How to get API keys"):
        st.markdown("""
        - **Anthropic**: [console.anthropic.com](https://console.anthropic.com)
        - **Gemini**: [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
        - **Remove.bg**: [remove.bg/api](https://remove.bg/api)
        """)

# Main content area
st.header("📤 Upload Images")

uploaded_files = st.file_uploader(
    "Choose images to process...",
    type=['png', 'jpg', 'jpeg', 'webp'],
    accept_multiple_files=True,
    help="Select multiple product photos to enhance"
)

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} images selected")
    
    # Display thumbnails
    st.subheader("📸 Selected Images")
    cols = st.columns(min(len(uploaded_files), 5))
    for idx, file in enumerate(uploaded_files[:5]):
        with cols[idx]:
            image = Image.open(file)
            st.image(image, caption=file.name[:20], use_container_width=True)
    
    if len(uploaded_files) > 5:
        st.info(f"...and {len(uploaded_files) - 5} more images")
    
    # Instructions
    st.subheader("✏️ Batch Instructions")
    instructions = st.text_area(
        "Enter editing instructions (applied to all images):",
        value="Enhance the product photo for e-commerce. Make it more vibrant and professional.",
        height=100,
        help="Same instructions will be applied to all images"
    )
    
    # Process button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        process_button = st.button("🚀 Process All Images", type="primary", use_container_width=True)

# Processing section
if uploaded_files and process_button:
    if not anthropic_key:
        st.error("⚠️ Please enter your Anthropic API key in the sidebar")
    elif use_gemini and not gemini_key:
        st.error("⚠️ Please enter your Gemini API key in the sidebar")
    else:
        # Set environment variables
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key
        os.environ["GEMINI_API_KEY"] = gemini_key
        if removebg_key:
            os.environ["REMOVE_BG_API_KEY"] = removebg_key
        
        st.markdown("---")
        st.header("⚙️ Processing Images")
        
        # Progress tracking
        progress_bar = st.progress(0, text="Starting batch processing...")
        status_text = st.empty()
        results_container = st.container()
        
        # Process images
        with tempfile.TemporaryDirectory() as temp_dir:
            results = []
            failed_images = []
            
            async def process_image_async(file, idx, total):
                """Process a single image asynchronously"""
                try:
                    # Save uploaded file
                    input_path = Path(temp_dir) / f"input_{idx}_{file.name}"
                    with open(input_path, "wb") as f:
                        f.write(file.getbuffer())
                    
                    # Update progress
                    status_text.text(f"Processing {file.name} ({idx + 1}/{total})...")
                    
                    # Process the image
                    result = await process_single_image_enhanced(
                        image_path=str(input_path),
                        custom_instructions=instructions,
                        output_dir=temp_dir
                    )
                    
                    if result.get("final_image"):
                        return {
                            "success": True,
                            "original_name": file.name,
                            "output_path": result.get("final_image"),
                            "quality": result.get('final_quality', result.get('quality_score', 'N/A'))
                        }
                    else:
                        return {
                            "success": False,
                            "original_name": file.name,
                            "error": result.get('error', 'Unknown error')
                        }
                        
                except Exception as e:
                    return {
                        "success": False,
                        "original_name": file.name,
                        "error": str(e)
                    }
            
            async def process_batch():
                """Process all images with concurrency control"""
                tasks = []
                for idx, file in enumerate(uploaded_files):
                    task = process_image_async(file, idx, len(uploaded_files))
                    tasks.append(task)
                
                # Process with limited concurrency
                all_results = []
                for i in range(0, len(tasks), max_concurrent):
                    batch = tasks[i:i + max_concurrent]
                    batch_results = await asyncio.gather(*batch)
                    all_results.extend(batch_results)
                    
                    # Update progress
                    progress = min((i + max_concurrent) / len(tasks), 1.0)
                    progress_bar.progress(progress, text=f"Processed {min(i + max_concurrent, len(tasks))}/{len(tasks)} images")
                
                return all_results
            
            # Run the batch processing
            with st.spinner(f"Processing {len(uploaded_files)} images..."):
                results = asyncio.run(process_batch())
            
            # Show results
            progress_bar.progress(1.0, text="✅ Processing complete!")
            status_text.text("")
            
            # Separate successful and failed
            successful = [r for r in results if r["success"]]
            failed = [r for r in results if not r["success"]]
            
            # Display summary
            st.markdown("---")
            st.header("📊 Results Summary")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Processed", len(results))
            with col2:
                st.metric("Successful", len(successful), delta=f"{len(successful)/len(results)*100:.0f}%")
            with col3:
                st.metric("Failed", len(failed))
            
            # Create ZIP file with all successful results
            if successful:
                st.subheader("📦 Download Results")
                
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for result in successful:
                        if Path(result["output_path"]).exists():
                            # Add to ZIP with enhanced name
                            output_name = f"enhanced_{Path(result['original_name']).stem}.webp"
                            zip_file.write(result["output_path"], output_name)
                
                zip_buffer.seek(0)
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.download_button(
                        label="⬇️ Download All Enhanced Images (ZIP)",
                        data=zip_buffer,
                        file_name=f"enhanced_photos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
            
            # Show individual results
            if successful:
                st.subheader("✅ Successfully Processed")
                
                # Display in grid
                cols_per_row = 3
                for i in range(0, len(successful), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, col in enumerate(cols):
                        if i + j < len(successful):
                            result = successful[i + j]
                            with col:
                                if Path(result["output_path"]).exists():
                                    enhanced_img = Image.open(result["output_path"])
                                    st.image(enhanced_img, caption=f"{result['original_name'][:20]}", use_container_width=True)
                                    
                                    quality = result.get('quality', 'N/A')
                                    if quality != 'N/A':
                                        st.caption(f"Quality: {quality}/10")
                                    
                                    # Individual download
                                    with open(result["output_path"], "rb") as f:
                                        st.download_button(
                                            label="Download",
                                            data=f.read(),
                                            file_name=f"enhanced_{result['original_name']}",
                                            mime="image/webp",
                                            key=f"download_{i}_{j}",
                                            use_container_width=True
                                        )
            
            # Show failed images
            if failed:
                st.subheader("❌ Failed to Process")
                for result in failed:
                    st.error(f"**{result['original_name']}**: {result['error']}")
            
            # Store results in session state
            st.session_state.batch_results = results
            st.session_state.processing_complete = True

# Tips section
st.markdown("---")
st.subheader("💡 Tips for Batch Processing")
st.info("""
- **File Naming**: Enhanced files will be prefixed with "enhanced_"
- **Format**: All outputs are in WebP format for best quality/size ratio
- **Large Batches**: For 20+ images, consider processing in smaller batches
- **API Limits**: Be mindful of your API rate limits and quotas
- **Best Results**: Use consistent lighting and backgrounds across your product photos
""")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    Made with ❤️ for Doug using LangGraph, Claude Sonnet 4, and Gemini 2.5 Flash<br>
    <a href='https://github.com/pranavchavda/langgraph-photo-editor'>GitHub</a> | 
    Batch processing for productivity!
</div>
""", unsafe_allow_html=True)