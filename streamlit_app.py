"""
Doug's Photo Editor - Single Page App with Batch Mode Toggle
Process single images or multiple images in batch
"""

import streamlit as st
import asyncio
from pathlib import Path
import tempfile
import shutil
from PIL import Image
import os
from datetime import datetime
import streamlit.components.v1 as components
import zipfile
import io

# Import our existing workflow and lens corrections
from src.workflow_enhanced import process_single_image_enhanced
from src.lens_corrections import get_lens_options, apply_lens_corrections, get_focal_length_options

# Page config
st.set_page_config(
    page_title="Doug's Photo Editor",
    page_icon="📸",
    layout="wide"
)

# Initialize session state
if 'processed_image' not in st.session_state:
    st.session_state.processed_image = None
if 'processed_image_data' not in st.session_state:
    st.session_state.processed_image_data = None
if 'processed_filename' not in st.session_state:
    st.session_state.processed_filename = None
if 'processing_metrics' not in st.session_state:
    st.session_state.processing_metrics = None
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = []
if 'api_keys' not in st.session_state:
    # Initialize with empty values
    st.session_state.api_keys = {
        'anthropic': '',
        'gemini': '',
        'removebg': ''
    }
if 'keys_loaded' not in st.session_state:
    st.session_state.keys_loaded = False

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
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 4px;
        color: #155724;
    }
</style>
""", unsafe_allow_html=True)

# JavaScript for localStorage - improved persistence
local_storage_js = """
<script>
(function() {
    // Save keys when they change
    const saveToStorage = () => {
        const inputs = document.querySelectorAll('input[type="password"]');
        if (inputs[0] && inputs[0].value) {
            localStorage.setItem('doug_anthropic', inputs[0].value);
        }
        if (inputs[1] && inputs[1].value) {
            localStorage.setItem('doug_gemini', inputs[1].value);
        }
        if (inputs[2] && inputs[2].value) {
            localStorage.setItem('doug_removebg', inputs[2].value);
        }
    };
    
    // Load saved keys
    const loadFromStorage = () => {
        const anthropic = localStorage.getItem('doug_anthropic');
        const gemini = localStorage.getItem('doug_gemini');
        const removebg = localStorage.getItem('doug_removebg');
        
        const inputs = document.querySelectorAll('input[type="password"]');
        if (inputs[0] && anthropic) {
            inputs[0].value = anthropic;
            inputs[0].dispatchEvent(new Event('input', {bubbles: true}));
        }
        if (inputs[1] && gemini) {
            inputs[1].value = gemini;
            inputs[1].dispatchEvent(new Event('input', {bubbles: true}));
        }
        if (inputs[2] && removebg) {
            inputs[2].value = removebg;
            inputs[2].dispatchEvent(new Event('input', {bubbles: true}));
        }
    };
    
    // Try loading multiple times to ensure inputs are ready
    let attempts = 0;
    const tryLoad = setInterval(() => {
        const inputs = document.querySelectorAll('input[type="password"]');
        if (inputs.length >= 3 || attempts > 10) {
            loadFromStorage();
            
            // Add save listeners
            inputs.forEach(input => {
                input.addEventListener('input', saveToStorage);
                input.addEventListener('change', saveToStorage);
            });
            
            clearInterval(tryLoad);
        }
        attempts++;
    }, 200);
})();
</script>
"""

components.html(local_storage_js, height=0)

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
        help="Required for image analysis and quality control"
    )
    
    gemini_key = st.text_input(
        "Gemini API Key", 
        type="password",
        key="gemini_key_input",
        value=st.session_state.api_keys['gemini'],
        help="Required for AI-powered image editing"
    )
    
    removebg_key = st.text_input(
        "Remove.bg API Key (Optional)", 
        type="password",
        key="removebg_key_input",
        value=st.session_state.api_keys['removebg'],
        help="Optional - for professional background removal"
    )
    
    # Update session state
    st.session_state.api_keys['anthropic'] = anthropic_key
    st.session_state.api_keys['gemini'] = gemini_key  
    st.session_state.api_keys['removebg'] = removebg_key
    
    st.subheader("Processing Options")
    use_gemini = st.checkbox("Use Gemini 2.5 Flash", value=True)
    remove_background = st.checkbox("Remove Background", value=False)
    
    st.subheader("📷 Lens Corrections")
    lens_options = get_lens_options()
    selected_lens = st.selectbox(
        "Select lens used (or auto-detect):",
        lens_options,
        index=len(lens_options) - 1,  # Default to auto-detect
        help="Select your Sony lens for automatic corrections like Lightroom"
    )
    
    # Show focal length selector for zoom lenses
    focal_length = None
    if selected_lens and "mm F" in selected_lens and "-" in selected_lens:
        # It's a zoom lens, show focal length options
        focal_options = get_focal_length_options(selected_lens)
        if focal_options:
            focal_length = st.select_slider(
                "Focal length used:",
                options=focal_options,
                value=focal_options[len(focal_options)//2]  # Default to middle
            )
    
    st.info("💡 Tip: API keys are saved in your browser and persist across sessions")
    
    with st.expander("🔑 How to get API keys"):
        st.markdown("""
        - **Anthropic**: [console.anthropic.com](https://console.anthropic.com)
        - **Gemini**: [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
        - **Remove.bg**: [remove.bg/api](https://remove.bg/api)
        """)

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
    st.title("Doug's Photo Editor")
    st.markdown("""
    Upload your product photos and let our multi-agent AI pipeline optimize them for e-commerce!
    Powered by Claude Sonnet 4 and Gemini 2.5 Flash.
    """)

# Mode selector
st.markdown("---")
mode = st.radio(
    "Choose Processing Mode:",
    ["🖼️ Single Image", "📦 Batch Processing"],
    horizontal=True,
    help="Single Image: Process one image at a time | Batch: Process multiple images at once"
)

st.markdown("---")

# Single Image Mode
if mode == "🖼️ Single Image":
    st.header("📤 Upload Image")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📷 Input")
        uploaded_file = st.file_uploader(
            "Choose an image to enhance...",
            type=['png', 'jpg', 'jpeg', 'webp'],
            key="single_upload"
        )
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Original Image", use_container_width=True)
            
            st.subheader("✏️ Instructions")
            instructions = st.text_area(
                "How would you like to enhance this image?",
                value="Enhance this product photo for e-commerce. Make it more vibrant and professional. Ensure the product stands out.",
                height=100
            )
            
            process_button = st.button("🚀 Process Image", type="primary", use_container_width=True)
    
    with col2:
        st.subheader("📥 Result")
        
        # Display stored result if available
        if st.session_state.processed_image is not None:
            st.image(st.session_state.processed_image, caption="Enhanced Image", use_container_width=True)
            
            # Prominent download button with custom styling
            st.markdown("""
            <style>
            .download-section > div > button {
                background-color: #4CAF50 !important;
                color: white !important;
                font-size: 18px !important;
                font-weight: bold !important;
                padding: 12px !important;
                border-radius: 8px !important;
                margin-top: 10px !important;
                margin-bottom: 10px !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="download-section">', unsafe_allow_html=True)
            st.download_button(
                label="💾 ⬇️ DOWNLOAD ENHANCED IMAGE ⬇️ 💾",
                data=st.session_state.processed_image_data,
                file_name=st.session_state.processed_filename,
                mime="image/webp",
                use_container_width=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.session_state.processing_metrics:
                st.subheader("📊 Processing Metrics")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Quality Score", st.session_state.processing_metrics['quality'])
                with col_b:
                    st.metric("Strategy Used", st.session_state.processing_metrics['strategy'])
        
        if uploaded_file and process_button:
            if not anthropic_key:
                st.error("⚠️ Please enter your Anthropic API key in the sidebar")
            elif use_gemini and not gemini_key:
                st.error("⚠️ Please enter your Gemini API key in the sidebar")
            else:
                os.environ["ANTHROPIC_API_KEY"] = anthropic_key
                os.environ["GEMINI_API_KEY"] = gemini_key
                if removebg_key:
                    os.environ["REMOVE_BG_API_KEY"] = removebg_key
                
                with st.spinner("🔄 Processing your image..."):
                    try:
                        with tempfile.TemporaryDirectory() as temp_dir:
                            input_path = Path(temp_dir) / uploaded_file.name
                            with open(input_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            # Apply lens corrections first if applicable
                            corrected_path = str(Path(temp_dir) / f"corrected_{uploaded_file.name}")
                            lens_result = apply_lens_corrections(
                                str(input_path),
                                corrected_path,
                                selected_lens=selected_lens if selected_lens != "None (Auto-detect from EXIF)" else None,
                                focal_length=float(focal_length.replace('mm', '')) if focal_length else None
                            )
                            
                            # Use corrected image if corrections were applied
                            if lens_result.get('corrections_applied'):
                                st.info(f"📷 Applied lens corrections: {lens_result.get('message', '')}")
                                process_path = corrected_path
                            else:
                                process_path = str(input_path)
                            
                            result = asyncio.run(process_single_image_enhanced(
                                image_path=process_path,
                                custom_instructions=instructions,
                                output_dir=temp_dir
                            ))
                            
                            if result.get("final_image"):
                                output_path = result.get("final_image")
                                if output_path and Path(output_path).exists():
                                    result_image = Image.open(output_path)
                                    
                                    st.session_state.processed_image = result_image
                                    with open(output_path, "rb") as f:
                                        st.session_state.processed_image_data = f.read()
                                    st.session_state.processed_filename = f"enhanced_{uploaded_file.name}"
                                    
                                    quality = result.get('final_quality', result.get('quality_score', 'N/A'))
                                    if quality != 'N/A':
                                        quality_display = f"{quality}/10"
                                    else:
                                        quality_display = quality
                                    strategy = result.get('strategy', 'Enhanced AI Pipeline')
                                    st.session_state.processing_metrics = {
                                        'quality': quality_display,
                                        'strategy': strategy
                                    }
                                    
                                    st.success("✅ Image processed successfully!")
                                    st.rerun()
                                else:
                                    st.error("❌ Output image not found")
                            else:
                                error_msg = result.get('error', 'Unknown error occurred')
                                st.error(f"❌ Processing failed: {error_msg}")
                                
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

# Batch Processing Mode
else:  # mode == "📦 Batch Processing"
    st.header("📤 Upload Multiple Images")
    
    uploaded_files = st.file_uploader(
        "Choose images to process...",
        type=['png', 'jpg', 'jpeg', 'webp'],
        accept_multiple_files=True,
        key="batch_upload"
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
        
        # Batch settings
        st.subheader("⚙️ Batch Settings")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            batch_lens = st.selectbox(
                "Lens used for all images:",
                get_lens_options(),
                index=len(get_lens_options()) - 1,  # Default to auto-detect
                key="batch_lens",
                help="Apply same lens corrections to all images"
            )
            # Show focal length for zoom lenses
            batch_focal = None
            if batch_lens and "mm F" in batch_lens and "-" in batch_lens:
                focal_opts = get_focal_length_options(batch_lens)
                if focal_opts:
                    batch_focal = st.select_slider(
                        "Focal length:",
                        options=focal_opts,
                        value=focal_opts[len(focal_opts)//2],
                        key="batch_focal"
                    )
        
        with col2:
            max_concurrent = st.slider(
                "Concurrent Processing",
                min_value=1,
                max_value=5,
                value=2,
                help="Process multiple images at once"
            )
        
        with col3:
            st.metric("Total Images", len(uploaded_files))
            estimated_time = (len(uploaded_files) / max_concurrent) * 30  # ~30s per image
            st.caption(f"Est. time: {int(estimated_time)}s")
        
        st.subheader("✏️ Batch Instructions")
        batch_instructions = st.text_area(
            "Enter editing instructions (applied to all images):",
            value="Enhance the product photo for e-commerce. Make it more vibrant and professional.",
            height=100
        )
        
        process_batch_button = st.button("🚀 Process All Images", type="primary", use_container_width=True)
        
        if process_batch_button:
            if not anthropic_key:
                st.error("⚠️ Please enter your Anthropic API key in the sidebar")
            elif use_gemini and not gemini_key:
                st.error("⚠️ Please enter your Gemini API key in the sidebar")
            else:
                os.environ["ANTHROPIC_API_KEY"] = anthropic_key
                os.environ["GEMINI_API_KEY"] = gemini_key
                if removebg_key:
                    os.environ["REMOVE_BG_API_KEY"] = removebg_key
                
                st.markdown("---")
                st.header("⚙️ Processing Images")
                
                progress_bar = st.progress(0, text="Starting batch processing...")
                status_text = st.empty()
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    results = []
                    
                    async def process_image_async(file, idx, total):
                        try:
                            input_path = Path(temp_dir) / f"input_{idx}_{file.name}"
                            with open(input_path, "wb") as f:
                                f.write(file.getbuffer())
                            
                            status_text.text(f"Processing {file.name} ({idx + 1}/{total})...")
                            
                            # Apply lens corrections first
                            corrected_path = str(Path(temp_dir) / f"corrected_{idx}_{file.name}")
                            lens_result = apply_lens_corrections(
                                str(input_path),
                                corrected_path,
                                selected_lens=batch_lens if batch_lens != "None (Auto-detect from EXIF)" else None,
                                focal_length=float(batch_focal.replace('mm', '')) if batch_focal else None
                            )
                            
                            # Use corrected image if corrections were applied
                            process_path = corrected_path if lens_result.get('corrections_applied') else str(input_path)
                            
                            result = await process_single_image_enhanced(
                                image_path=process_path,
                                custom_instructions=batch_instructions,
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
                        tasks = []
                        for idx, file in enumerate(uploaded_files):
                            task = process_image_async(file, idx, len(uploaded_files))
                            tasks.append(task)
                        
                        all_results = []
                        for i in range(0, len(tasks), max_concurrent):
                            batch = tasks[i:i + max_concurrent]
                            batch_results = await asyncio.gather(*batch)
                            all_results.extend(batch_results)
                            
                            progress = min((i + max_concurrent) / len(tasks), 1.0)
                            progress_bar.progress(progress, text=f"Processed {min(i + max_concurrent, len(tasks))}/{len(tasks)} images")
                        
                        return all_results
                    
                    with st.spinner(f"Processing {len(uploaded_files)} images..."):
                        results = asyncio.run(process_batch())
                    
                    progress_bar.progress(1.0, text="✅ Processing complete!")
                    status_text.text("")
                    
                    successful = [r for r in results if r["success"]]
                    failed = [r for r in results if not r["success"]]
                    
                    st.markdown("---")
                    st.header("📊 Results Summary")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Processed", len(results))
                    with col2:
                        st.metric("Successful", len(successful), delta=f"{len(successful)/len(results)*100:.0f}%")
                    with col3:
                        st.metric("Failed", len(failed))
                    
                    if successful:
                        # Make the download section very prominent
                        st.markdown("---")
                        st.markdown("<h1 style='text-align: center; color: #4CAF50;'>🎉 Your Images Are Ready!</h1>", unsafe_allow_html=True)
                        
                        # Create ZIP file
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for result in successful:
                                if Path(result["output_path"]).exists():
                                    output_name = f"enhanced_{Path(result['original_name']).stem}.webp"
                                    zip_file.write(result["output_path"], output_name)
                        
                        zip_buffer.seek(0)
                        
                        # Large prominent download section
                        col1, col2, col3 = st.columns([1, 3, 1])
                        with col2:
                            # Custom CSS for the big button
                            st.markdown("""
                            <style>
                            .big-download-button > button {
                                background-color: #4CAF50 !important;
                                color: white !important;
                                font-size: 24px !important;
                                font-weight: bold !important;
                                padding: 20px !important;
                                border-radius: 10px !important;
                                border: 3px solid #45a049 !important;
                                box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
                                transition: all 0.3s !important;
                            }
                            .big-download-button > button:hover {
                                background-color: #45a049 !important;
                                box-shadow: 0 8px 16px rgba(0,0,0,0.3) !important;
                                transform: translateY(-2px) !important;
                            }
                            </style>
                            """, unsafe_allow_html=True)
                            
                            # The big download button
                            st.markdown('<div class="big-download-button">', unsafe_allow_html=True)
                            st.download_button(
                                label="📦⬇️ DOWNLOAD ALL IMAGES (ZIP) ⬇️📦",
                                data=zip_buffer,
                                file_name=f"enhanced_photos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                                mime="application/zip",
                                use_container_width=True,
                                key="big_download_btn"
                            )
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Additional helpful info
                            st.success(f"✅ {len(successful)} images ready for download")
                            st.info(f"💾 File size: ~{len(zip_buffer.getvalue()) / 1024 / 1024:.1f} MB")
                        
                        st.markdown("---")
                        
                        st.subheader("✅ Successfully Processed Images")
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
                    
                    if failed:
                        st.subheader("❌ Failed to Process")
                        for result in failed:
                            st.error(f"**{result['original_name']}**: {result['error']}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    Made with ❤️ for Doug using LangGraph, Claude Sonnet 4, and Gemini 2.5 Flash<br>
    <a href='https://github.com/pranavchavda/langgraph-photo-editor'>GitHub</a> | 
    Your API keys never leave your browser
</div>
""", unsafe_allow_html=True)