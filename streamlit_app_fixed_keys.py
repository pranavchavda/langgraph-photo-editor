"""
Doug's Photo Editor - With Persistent API Keys
"""

import streamlit as st
import asyncio
from pathlib import Path
import tempfile
from PIL import Image
import os
import streamlit.components.v1 as components
import zipfile
import io
from datetime import datetime

# Import our existing workflow
from src.workflow_enhanced import process_single_image_enhanced

# Try to use advanced lens corrections, fall back to basic if not available
try:
    from src.lens_corrections_advanced import apply_lens_corrections, get_lens_options, get_focal_length_options
    LENS_CORRECTION_METHOD = "advanced (lensfunpy)"
except ImportError:
    from src.lens_corrections import apply_lens_corrections, get_lens_options, get_focal_length_options
    LENS_CORRECTION_METHOD = "basic (ImageMagick)"

# Page config
st.set_page_config(
    page_title="Doug's Photo Editor",
    page_icon="📸",
    layout="wide"
)

# Initialize persistent session state for API keys
if 'api_keys_dict' not in st.session_state:
    st.session_state.api_keys_dict = {
        'anthropic': '',
        'gemini': '',
        'removebg': ''
    }

# Initialize other session state
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

# JavaScript for bi-directional localStorage sync
storage_js = f"""
<script>
(function() {{
    // Function to load keys from localStorage
    function loadKeys() {{
        const stored = {{
            anthropic: localStorage.getItem('doug_anthropic') || '',
            gemini: localStorage.getItem('doug_gemini') || '',
            removebg: localStorage.getItem('doug_removebg') || ''
        }};
        
        console.log('Found in localStorage:', {{
            anthropic: !!stored.anthropic,
            gemini: !!stored.gemini,
            removebg: !!stored.removebg
        }});
        
        // Find and populate the input fields
        setTimeout(() => {{
            const inputs = parent.document.querySelectorAll('input[type="password"]');
            if (inputs.length >= 3) {{
                // Only set if the stored value exists and input is empty
                if (stored.anthropic && !inputs[0].value) {{
                    inputs[0].value = stored.anthropic;
                    // Trigger Streamlit's change detection
                    const event = new Event('input', {{ bubbles: true }});
                    inputs[0].dispatchEvent(event);
                }}
                if (stored.gemini && !inputs[1].value) {{
                    inputs[1].value = stored.gemini;
                    const event = new Event('input', {{ bubbles: true }});
                    inputs[1].dispatchEvent(event);
                }}
                if (stored.removebg && !inputs[2].value) {{
                    inputs[2].value = stored.removebg;
                    const event = new Event('input', {{ bubbles: true }});
                    inputs[2].dispatchEvent(event);
                }}
            }}
        }}, 100);
        
        // Try again after a delay
        setTimeout(() => {{
            const inputs = parent.document.querySelectorAll('input[type="password"]');
            if (inputs.length >= 3) {{
                if (stored.anthropic && !inputs[0].value) {{
                    inputs[0].value = stored.anthropic;
                    inputs[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
                if (stored.gemini && !inputs[1].value) {{
                    inputs[1].value = stored.gemini;
                    inputs[1].dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
                if (stored.removebg && !inputs[2].value) {{
                    inputs[2].value = stored.removebg;
                    inputs[2].dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
            }}
        }}, 1000);
    }}
    
    // Function to save keys to localStorage
    function saveKeys() {{
        const inputs = parent.document.querySelectorAll('input[type="password"]');
        if (inputs.length >= 3) {{
            if (inputs[0].value) localStorage.setItem('doug_anthropic', inputs[0].value);
            if (inputs[1].value) localStorage.setItem('doug_gemini', inputs[1].value);
            if (inputs[2].value) localStorage.setItem('doug_removebg', inputs[2].value);
            console.log('Saved to localStorage');
        }}
    }}
    
    // Load on startup
    loadKeys();
    
    // Set up save listeners
    setTimeout(() => {{
        const inputs = parent.document.querySelectorAll('input[type="password"]');
        inputs.forEach(input => {{
            input.addEventListener('blur', saveKeys);
            input.addEventListener('change', saveKeys);
        }});
    }}, 2000);
    
    // Also save the current session state values if they exist
    const sessionAnthropric = '{st.session_state.api_keys_dict.get("anthropic", "")}';
    const sessionGemini = '{st.session_state.api_keys_dict.get("gemini", "")}';
    const sessionRemovebg = '{st.session_state.api_keys_dict.get("removebg", "")}';
    
    if (sessionAnthropric) localStorage.setItem('doug_anthropic', sessionAnthropric);
    if (sessionGemini) localStorage.setItem('doug_gemini', sessionGemini);
    if (sessionRemovebg) localStorage.setItem('doug_removebg', sessionRemovebg);
}})();
</script>
"""

# Inject the localStorage manager
components.html(storage_js, height=0)

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("API Keys")
    st.markdown("*Your API keys are stored locally in your browser*")
    
    # Callback functions to update the persistent dict
    def update_anthropic():
        st.session_state.api_keys_dict['anthropic'] = st.session_state.anthropic_input
    
    def update_gemini():
        st.session_state.api_keys_dict['gemini'] = st.session_state.gemini_input
    
    def update_removebg():
        st.session_state.api_keys_dict['removebg'] = st.session_state.removebg_input
    
    anthropic_key = st.text_input(
        "Anthropic API Key", 
        type="password",
        key="anthropic_input",
        value=st.session_state.api_keys_dict.get('anthropic', ''),
        on_change=update_anthropic,
        help="Required for image analysis and quality control"
    )
    
    gemini_key = st.text_input(
        "Gemini API Key", 
        type="password",
        key="gemini_input",
        value=st.session_state.api_keys_dict.get('gemini', ''),
        on_change=update_gemini,
        help="Required for AI-powered image editing"
    )
    
    removebg_key = st.text_input(
        "Remove.bg API Key (Optional)", 
        type="password",
        key="removebg_input",
        value=st.session_state.api_keys_dict.get('removebg', ''),
        on_change=update_removebg,
        help="Optional - for professional background removal"
    )
    
    st.subheader("Processing Options")
    use_gemini = st.checkbox("Use Gemini 2.5 Flash", value=True)
    remove_background = st.checkbox("Remove Background", value=False)
    
    st.subheader("📷 Lens Corrections")
    lens_options = get_lens_options()
    selected_lens = st.selectbox(
        "Select lens used (or auto-detect):",
        lens_options,
        index=len(lens_options) - 1,
        help="Select your Sony lens for automatic corrections like Lightroom"
    )
    
    focal_length = None
    if selected_lens and "mm F" in selected_lens and "-" in selected_lens:
        focal_options = get_focal_length_options(selected_lens)
        if focal_options:
            focal_length = st.select_slider(
                "Focal length used:",
                options=focal_options,
                value=focal_options[len(focal_options)//2]
            )
    
    st.info("💡 Tip: API keys are saved in your browser and persist across sessions")
    st.caption(f"🔧 Lens corrections: {LENS_CORRECTION_METHOD}")
    
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
        st.markdown("# 📸")

with col_title:
    st.title("Doug's Photo Editor")
    st.markdown("*Professional e-commerce photo optimization powered by AI*")

# Mode selector
mode = st.radio(
    "Choose processing mode:",
    ["🖼️ Single Image", "📦 Batch Processing"],
    horizontal=True,
    key="mode_selector"
)

st.markdown("---")

# Single Image Mode
if mode == "🖼️ Single Image":
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("📤 Upload Image")
        uploaded_file = st.file_uploader(
            "Choose an image to enhance...",
            type=['png', 'jpg', 'jpeg', 'webp'],
            key="single_upload"
        )
        
        instructions = st.text_area(
            "Custom instructions (optional)",
            placeholder="E.g., 'Make chrome more vibrant, enhance shadows'",
            height=100,
            key="instructions"
        )
        
        process_button = st.button("🚀 Process Image", type="primary", key="process_single")
        
        if uploaded_file:
            st.image(uploaded_file, caption="Original Image", use_column_width=True)
    
    with col2:
        st.header("✨ Enhanced Result")
        
        if st.session_state.processed_image:
            st.image(st.session_state.processed_image, caption="Enhanced Image", use_column_width=True)
            
            if st.session_state.processing_metrics:
                col_metric1, col_metric2 = st.columns(2)
                with col_metric1:
                    st.metric("Quality Score", st.session_state.processing_metrics['quality'])
                with col_metric2:
                    st.metric("Strategy", st.session_state.processing_metrics['strategy'])
            
            # Large download button
            st.markdown("""
            <style>
            .download-container > div > button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white !important;
                font-size: 20px !important;
                font-weight: bold !important;
                padding: 15px 30px !important;
                border-radius: 10px !important;
                border: none !important;
                width: 100% !important;
                margin-top: 20px !important;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            with st.container():
                col_download = st.columns([1, 3, 1])[1]
                with col_download:
                    st.markdown('<div class="download-container">', unsafe_allow_html=True)
                    st.download_button(
                        label="⬇️ Download Enhanced Image",
                        data=st.session_state.processed_image_data,
                        file_name=st.session_state.processed_filename,
                        mime="image/webp"
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("👈 Upload an image and click 'Process Image' to begin")
        
        if uploaded_file and process_button:
            # Get keys from persistent dict
            anthropic_key = st.session_state.api_keys_dict.get('anthropic', '')
            gemini_key = st.session_state.api_keys_dict.get('gemini', '')
            removebg_key = st.session_state.api_keys_dict.get('removebg', '')
            
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
                            
                            # Apply lens corrections first
                            corrected_path = str(Path(temp_dir) / f"corrected_{uploaded_file.name}")
                            lens_result = apply_lens_corrections(
                                str(input_path),
                                corrected_path,
                                selected_lens=selected_lens if selected_lens != "None (Auto-detect from EXIF)" else None,
                                focal_length=float(focal_length.replace('mm', '')) if focal_length else None
                            )
                            
                            if lens_result.get('corrections_applied'):
                                st.info(f"📷 Applied lens corrections: {lens_result.get('message', '')}")
                                process_path = corrected_path
                            elif lens_result.get('lens_used'):
                                if lens_result.get('detected_from_exif'):
                                    st.info(f"📷 Auto-detected lens: {lens_result.get('lens_used')} (from EXIF)")
                                st.warning(f"⚠️ {lens_result.get('reason', 'Corrections not applied')}")
                                process_path = str(input_path)
                            else:
                                if selected_lens == "None (Auto-detect from EXIF)":
                                    st.info("📷 No lens data found in EXIF, proceeding without lens corrections")
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
else:
    st.header("📦 Batch Processing")
    st.info("Batch processing mode - Upload multiple images to process them all at once")

st.markdown("---")
st.caption("Built with ❤️ using LangGraph, Claude Sonnet 4, and Gemini 2.5 Flash")