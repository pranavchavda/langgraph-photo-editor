"""
Streamlit Web Interface for LangGraph Photo Editor
For Doug and anyone who wants a simple web interface!
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

# Import our existing workflow
from src.workflow_enhanced import process_single_image_enhanced

# Page config
st.set_page_config(
    page_title="AI Photo Editor",
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
# Initialize session state for API keys
if 'api_keys' not in st.session_state:
    st.session_state.api_keys = {
        'anthropic': '',
        'gemini': '',
        'removebg': ''
    }
    
    # Try to get from environment/secrets as initial values
    try:
        # Check environment variables first
        if os.getenv('ANTHROPIC_API_KEY'):
            st.session_state.api_keys['anthropic'] = os.getenv('ANTHROPIC_API_KEY')
        if os.getenv('GEMINI_API_KEY'):
            st.session_state.api_keys['gemini'] = os.getenv('GEMINI_API_KEY')
        if os.getenv('REMOVE_BG_API_KEY'):
            st.session_state.api_keys['removebg'] = os.getenv('REMOVE_BG_API_KEY')
            
        # Override with Streamlit secrets if available
        if 'ANTHROPIC_API_KEY' in st.secrets:
            st.session_state.api_keys['anthropic'] = st.secrets['ANTHROPIC_API_KEY']
        if 'GEMINI_API_KEY' in st.secrets:
            st.session_state.api_keys['gemini'] = st.secrets['GEMINI_API_KEY']
        if 'REMOVE_BG_API_KEY' in st.secrets:
            st.session_state.api_keys['removebg'] = st.secrets['REMOVE_BG_API_KEY']
    except:
        pass  # No secrets configured, localStorage will handle it

# Custom CSS and localStorage JavaScript
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

# JavaScript to handle localStorage
components.html("""
<script>
(function() {
    // Function to get stored keys
    function getStoredKeys() {
        return {
            anthropic: localStorage.getItem('photoEditor_anthropic') || '',
            gemini: localStorage.getItem('photoEditor_gemini') || '',
            removebg: localStorage.getItem('photoEditor_removebg') || ''
        };
    }
    
    // Function to save keys
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
    
    // Auto-populate from localStorage on load
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
    
    // Save on input change
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

# Logo and title section
col_logo, col_title = st.columns([1, 4])

with col_logo:
    # Display logo if it exists
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

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("API Keys")
    st.markdown("*Your API keys are stored locally in your browser*")
    
    # API key inputs with session state persistence
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
    
    # Update session state when keys change and trigger localStorage save
    if anthropic_key != st.session_state.api_keys['anthropic']:
        st.session_state.api_keys['anthropic'] = anthropic_key
        # JavaScript will automatically save to localStorage
    if gemini_key != st.session_state.api_keys['gemini']:
        st.session_state.api_keys['gemini'] = gemini_key
        # JavaScript will automatically save to localStorage
    if removebg_key != st.session_state.api_keys['removebg']:
        st.session_state.api_keys['removebg'] = removebg_key
        # JavaScript will automatically save to localStorage
    
    st.subheader("Processing Options")
    use_gemini = st.checkbox("Use Gemini 2.5 Flash", value=True)
    remove_background = st.checkbox("Remove Background", value=False)
    
    st.info("💡 Tip: API keys are saved in your browser and persist across sessions")
    
    # Add links to get API keys
    with st.expander("🔑 How to get API keys"):
        st.markdown("""
        - **Anthropic (Claude)**: [console.anthropic.com](https://console.anthropic.com)
        - **Google Gemini**: [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
        - **Remove.bg**: [remove.bg/api](https://remove.bg/api)
        """)

# Main content area
col1, col2 = st.columns(2)

with col1:
    st.header("📤 Upload Image")
    uploaded_file = st.file_uploader(
        "Choose an image...",
        type=['png', 'jpg', 'jpeg', 'webp'],
        help="Upload a product photo to enhance"
    )
    
    if uploaded_file is not None:
        # Display uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Original Image", use_container_width=True)
        
        # Instructions
        st.subheader("✏️ Instructions")
        instructions = st.text_area(
            "Enter your editing instructions:",
            value="Enhance the product photo for e-commerce. Make it more vibrant and professional.",
            height=100,
            help="Describe what changes you want to make to the image"
        )
        
        # Process button
        process_button = st.button("🚀 Process Image", type="primary")

with col2:
    st.header("📥 Result")
    
    # Display stored result if available
    if st.session_state.processed_image is not None:
        st.image(st.session_state.processed_image, caption="Enhanced Image", use_container_width=True)
        
        # Add download button
        st.download_button(
            label="⬇️ Download Enhanced Image",
            data=st.session_state.processed_image_data,
            file_name=st.session_state.processed_filename,
            mime="image/webp"
        )
        
        # Display metrics
        if st.session_state.processing_metrics:
            st.subheader("📊 Processing Metrics")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Quality Score", st.session_state.processing_metrics['quality'])
            with col_b:
                st.metric("Strategy Used", st.session_state.processing_metrics['strategy'])
    
    # Results placeholder for new processing
    result_placeholder = st.empty()
    progress_placeholder = st.empty()
    
    if uploaded_file and process_button:
        if not anthropic_key:
            st.error("⚠️ Please enter your Anthropic API key in the sidebar")
        elif use_gemini and not gemini_key:
            st.error("⚠️ Please enter your Gemini API key in the sidebar")
        else:
            # Set environment variables from session state
            os.environ["ANTHROPIC_API_KEY"] = anthropic_key
            os.environ["GEMINI_API_KEY"] = gemini_key
            if removebg_key:
                os.environ["REMOVE_BG_API_KEY"] = removebg_key
            
            # Create temp directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save uploaded file
                input_path = Path(temp_dir) / uploaded_file.name
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Process with workflow
                with st.spinner("Processing your image... This may take a minute"):
                    progress_bar = progress_placeholder.progress(0, text="Starting...")
                    
                    # Run the async workflow
                    try:
                        # Process the image
                        result = asyncio.run(process_single_image_enhanced(
                            image_path=str(input_path),
                            custom_instructions=instructions,
                            output_dir=temp_dir
                        ))
                        
                        if result.get("final_image"):
                            # Display result
                            output_path = result.get("final_image")
                            if output_path and Path(output_path).exists():
                                result_image = Image.open(output_path)
                                
                                # Store in session state for persistence
                                st.session_state.processed_image = result_image
                                with open(output_path, "rb") as f:
                                    st.session_state.processed_image_data = f.read()
                                st.session_state.processed_filename = f"enhanced_{uploaded_file.name}"
                                
                                # Store metrics
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
                                
                                # Show success message
                                st.success("✅ Image processed successfully!")
                                
                                # Force rerun to display from session state
                                st.rerun()
                            else:
                                st.error("❌ Output image not found")
                        else:
                            st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                    
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                    finally:
                        progress_placeholder.empty()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    Made with ❤️ for Doug using LangGraph, Claude Sonnet 4, and Gemini 2.5 Flash<br>
    <a href='https://github.com/pranavchavda/langgraph-photo-editor'>GitHub</a> | 
    Your API keys never leave your browser
</div>
""", unsafe_allow_html=True)