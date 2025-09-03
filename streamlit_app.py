"""
Doug's Photo Editor - Main Landing Page
Navigate between Single Image and Batch Processing modes
"""

import streamlit as st
from pathlib import Path
from PIL import Image

# Page config
st.set_page_config(
    page_title="Doug's Photo Editor",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .feature-card {
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 1rem 0;
        transition: transform 0.3s;
    }
    .feature-card:hover {
        transform: translateY(-5px);
    }
    h1 {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Logo and title
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # Display logo
    logo_path = Path("logo.jpeg")
    if logo_path.exists():
        logo_image = Image.open(logo_path)
        st.image(logo_image, width=200, use_container_width=False)
    
    st.markdown("<h1>Doug's Photo Editor</h1>", unsafe_allow_html=True)
    st.markdown("""
    <p style='text-align: center; font-size: 1.2em;'>
    AI-powered photo enhancement for e-commerce<br>
    Powered by Claude Sonnet 4 and Gemini 2.5 Flash
    </p>
    """, unsafe_allow_html=True)

st.markdown("---")

# Features section
st.header("🎯 Choose Your Processing Mode")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
    <h2>🖼️ Single Image Mode</h2>
    <p>Perfect for quick edits and testing</p>
    <ul style='text-align: left; padding-left: 20%;'>
        <li>Upload one image</li>
        <li>See results instantly</li>
        <li>Fine-tune instructions</li>
        <li>Download enhanced version</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🖼️ Go to Single Image Mode", type="primary", use_container_width=True):
        st.switch_page("pages/1_🖼️_Single_Image.py")

with col2:
    st.markdown("""
    <div class="feature-card">
    <h2>📦 Batch Processing</h2>
    <p>Process your entire catalog at once</p>
    <ul style='text-align: left; padding-left: 20%;'>
        <li>Upload multiple images</li>
        <li>Concurrent processing</li>
        <li>Progress tracking</li>
        <li>Download all as ZIP</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📦 Go to Batch Processing", type="primary", use_container_width=True):
        st.switch_page("pages/2_📦_Batch_Processing.py")

st.markdown("---")

# How it works section
st.header("🔄 How It Works")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("1️⃣ Upload")
    st.write("Select your product photos - single or multiple")

with col2:
    st.subheader("2️⃣ Process")
    st.write("AI analyzes and enhances your images automatically")

with col3:
    st.subheader("3️⃣ Download")
    st.write("Get professional, e-commerce ready photos")

st.markdown("---")

# Features grid
st.header("✨ Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("AI Models", "2", help="Claude Sonnet 4 + Gemini 2.5 Flash")
    st.caption("Dual AI for best results")

with col2:
    st.metric("Processing Speed", "~30s", help="Per image on average")
    st.caption("Fast cloud processing")

with col3:
    st.metric("Formats Supported", "4+", help="JPG, PNG, WebP, and more")
    st.caption("All major image formats")

st.markdown("---")

# Getting started section
st.header("🚀 Getting Started")

with st.expander("📝 First Time Setup"):
    st.markdown("""
    1. **Get your API Keys** (one-time setup):
       - [Anthropic (Claude)](https://console.anthropic.com) - For image analysis
       - [Google Gemini](https://makersuite.google.com/app/apikey) - For AI editing
       - [Remove.bg](https://remove.bg/api) (Optional) - For background removal
    
    2. **Enter Keys in Sidebar**:
       - Your keys are saved locally in your browser
       - They persist across sessions
       - Never sent to our servers
    
    3. **Choose Processing Mode**:
       - Single Image: For individual photos
       - Batch Processing: For multiple photos
    
    4. **Upload and Process**:
       - Select your images
       - Add instructions (or use defaults)
       - Click Process!
    """)

with st.expander("💡 Tips for Best Results"):
    st.markdown("""
    - **Good Lighting**: Start with well-lit product photos
    - **Clear Instructions**: Be specific about what you want
    - **Batch Similar Items**: Process similar products together
    - **API Limits**: Be mindful of your API quotas
    - **File Sizes**: Smaller files process faster (under 5MB recommended)
    """)

with st.expander("❓ Frequently Asked Questions"):
    st.markdown("""
    **Q: How many images can I process at once?**
    A: Up to 50 images in batch mode, though we recommend 10-20 for best performance.
    
    **Q: What format are the output images?**
    A: WebP format for best quality and file size. PNG if WebP isn't available.
    
    **Q: Are my images stored anywhere?**
    A: No, images are processed in temporary memory and deleted immediately after.
    
    **Q: Can I use custom instructions?**
    A: Yes! You can specify exactly how you want your images enhanced.
    
    **Q: What if processing fails?**
    A: The app will show which images failed and why. Usually it's API limits.
    """)

# Sidebar instructions
with st.sidebar:
    st.header("📍 Navigation")
    st.success("""
    ⬆️ **Click the page names above!**
    
    The navigation menu is at the top of this sidebar:
    • 🖼️ Single Image
    • 📦 Batch Processing
    """)
    
    st.header("🔑 API Keys")
    st.caption("Enter your keys on either page - they're shared and saved locally")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    Made with ❤️ for Doug using LangGraph, Claude Sonnet 4, and Gemini 2.5 Flash<br>
    <a href='https://github.com/pranavchavda/langgraph-photo-editor'>GitHub</a> | 
    Your API keys never leave your browser
</div>
""", unsafe_allow_html=True)