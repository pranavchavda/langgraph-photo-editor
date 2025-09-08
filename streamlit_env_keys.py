"""
Doug's Photo Editor - Using Environment Variable Persistence
"""

import streamlit as st
import os
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Doug's Photo Editor - Simple Key Management",
    page_icon="📸",
    layout="wide"
)

st.title("📸 Doug's Photo Editor")
st.markdown("### Simple API Key Management Solution")

# Create .env file if it doesn't exist
env_file = Path(".env.local")

# Function to load keys from .env file
def load_keys_from_env():
    keys = {'anthropic': '', 'gemini': '', 'removebg': ''}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('ANTHROPIC_API_KEY='):
                    keys['anthropic'] = line.split('=', 1)[1].strip()
                elif line.startswith('GEMINI_API_KEY='):
                    keys['gemini'] = line.split('=', 1)[1].strip()
                elif line.startswith('REMOVE_BG_API_KEY='):
                    keys['removebg'] = line.split('=', 1)[1].strip()
    return keys

# Function to save keys to .env file
def save_keys_to_env(anthropic, gemini, removebg):
    with open(env_file, 'w') as f:
        if anthropic:
            f.write(f"ANTHROPIC_API_KEY={anthropic}\n")
        if gemini:
            f.write(f"GEMINI_API_KEY={gemini}\n")
        if removebg:
            f.write(f"REMOVE_BG_API_KEY={removebg}\n")
    st.success("✅ Keys saved to .env.local file")

# Load existing keys
saved_keys = load_keys_from_env()

# Sidebar
with st.sidebar:
    st.header("⚙️ API Key Management")
    
    st.info("""
    **Solution**: Keys are saved to a local `.env.local` file
    - ✅ Survives page refreshes
    - ✅ Survives file uploads
    - ✅ No JavaScript needed
    - ✅ 100% reliable
    """)
    
    # Form for entering keys
    with st.form("api_keys_form"):
        anthropic_key = st.text_input(
            "Anthropic API Key",
            value=saved_keys['anthropic'],
            type="password",
            help="Required for image analysis"
        )
        
        gemini_key = st.text_input(
            "Gemini API Key",
            value=saved_keys['gemini'],
            type="password",
            help="Required for AI image editing"
        )
        
        removebg_key = st.text_input(
            "Remove.bg API Key",
            value=saved_keys['removebg'],
            type="password",
            help="Optional - for background removal"
        )
        
        save_button = st.form_submit_button("💾 Save Keys", type="primary")
        
        if save_button:
            save_keys_to_env(anthropic_key, gemini_key, removebg_key)
            # Set environment variables for current session
            if anthropic_key:
                os.environ["ANTHROPIC_API_KEY"] = anthropic_key
            if gemini_key:
                os.environ["GEMINI_API_KEY"] = gemini_key
            if removebg_key:
                os.environ["REMOVE_BG_API_KEY"] = removebg_key
            st.rerun()
    
    # Show current status
    if saved_keys['anthropic']:
        st.success("✅ Anthropic key loaded")
    if saved_keys['gemini']:
        st.success("✅ Gemini key loaded")
    if saved_keys['removebg']:
        st.success("✅ Remove.bg key loaded")

# Main content
col1, col2 = st.columns(2)

with col1:
    st.header("📤 Upload Image")
    uploaded_file = st.file_uploader(
        "Choose an image...",
        type=['png', 'jpg', 'jpeg', 'webp']
    )
    
    if uploaded_file:
        st.image(uploaded_file, caption="Original Image")
        
        if st.button("🚀 Process Image", type="primary"):
            if not saved_keys['anthropic']:
                st.error("Please save your Anthropic API key first")
            elif not saved_keys['gemini']:
                st.error("Please save your Gemini API key first")
            else:
                # Set environment variables
                os.environ["ANTHROPIC_API_KEY"] = saved_keys['anthropic']
                os.environ["GEMINI_API_KEY"] = saved_keys['gemini']
                if saved_keys['removebg']:
                    os.environ["REMOVE_BG_API_KEY"] = saved_keys['removebg']
                
                st.success("Ready to process! (Processing logic would go here)")

with col2:
    st.header("✨ Result")
    st.info("Upload an image and click Process to see results")

st.markdown("---")
st.markdown("""
### 🎯 How This Works

1. **Enter your API keys** in the sidebar form
2. **Click "Save Keys"** - they're saved to `.env.local` file
3. **Keys persist** across page refreshes and file uploads
4. **No JavaScript needed** - pure Python/Streamlit solution

The `.env.local` file is:
- Created in your project directory
- Git-ignored (add to .gitignore)
- Loaded automatically on page refresh
- 100% reliable
""")