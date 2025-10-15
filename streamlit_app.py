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
from streamlit_local_storage import LocalStorage

# Import our existing workflow
from src.workflow_enhanced import process_single_image_enhanced
from src.quality_config import get_quality_settings
try:
    from src.preview_utils import generate_preview_from_sliders
    PREVIEW_AVAILABLE = True
except ImportError:
    PREVIEW_AVAILABLE = False
    print("Preview utils not available")

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
if 'current_uploaded_file' not in st.session_state:
    st.session_state.current_uploaded_file = None
# Initialize LocalStorage
localS = LocalStorage()

# Initialize API keys in session state
if 'api_keys' not in st.session_state:
    st.session_state.api_keys = {'anthropic': '', 'gemini': '', 'removebg': ''}

# Try to load keys from localStorage (works locally, not on cloud)
# On Streamlit Cloud, localStorage doesn't work, so user must enter keys via UI
try:
    saved_anthropic = localS.getItem("doug_anthropic_key")
    saved_gemini = localS.getItem("doug_gemini_key")
    saved_removebg = localS.getItem("doug_removebg_key")

    # Update session state if we got values from localStorage
    # Note: Due to component rendering, values might be None on first load
    if saved_anthropic:
        st.session_state.api_keys['anthropic'] = saved_anthropic
    if saved_gemini:
        st.session_state.api_keys['gemini'] = saved_gemini
    if saved_removebg:
        st.session_state.api_keys['removebg'] = saved_removebg
except Exception as e:
    # localStorage doesn't work on Streamlit Cloud - user will enter keys via UI form
    print(f"ℹ️ localStorage not available (Streamlit Cloud mode): {e}")
    print("   Users will enter API keys via the UI form")

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
    .help-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# No need for complex JavaScript anymore - LocalStorage handles it!

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")

    st.subheader("API Keys")
    
    # Use a form so file uploads don't clear the keys
    with st.form("api_keys_form"):
        st.markdown("*Enter your API keys and click Save*")
        
        anthropic_key = st.text_input(
            "Anthropic API Key", 
            type="password",
            value=st.session_state.api_keys.get('anthropic', ''),
            help="Required for image analysis and quality control"
        )
        
        gemini_key = st.text_input(
            "Gemini API Key", 
            type="password",
            value=st.session_state.api_keys.get('gemini', ''),
            help="Required for AI-powered image editing"
        )
        
        removebg_key = st.text_input(
            "Remove.bg API Key (Optional)", 
            type="password",
            value=st.session_state.api_keys.get('removebg', ''),
            help="Optional - for professional background removal"
        )
        
        # Form submit button
        save_keys = st.form_submit_button("💾 Save Keys", type="primary")
        
        if save_keys:
            # Update session state
            st.session_state.api_keys['anthropic'] = anthropic_key
            st.session_state.api_keys['gemini'] = gemini_key
            st.session_state.api_keys['removebg'] = removebg_key
            
            # Save to localStorage using streamlit-local-storage
            # Each setItem needs a unique key for the component
            if anthropic_key:
                localS.setItem("doug_anthropic_key", anthropic_key, key="set_anthropic")
            if gemini_key:
                localS.setItem("doug_gemini_key", gemini_key, key="set_gemini")
            if removebg_key:
                localS.setItem("doug_removebg_key", removebg_key, key="set_removebg")
            
            st.success("✅ Keys saved to browser storage!")
    
    # Show current status outside the form
    if st.session_state.api_keys.get('anthropic'):
        st.success("✅ Anthropic key loaded")
    if st.session_state.api_keys.get('gemini'):
        st.success("✅ Gemini key loaded")
    if st.session_state.api_keys.get('removebg'):
        st.success("✅ Remove.bg key loaded")

    # Background Removal Method Selection
    st.subheader("🖼️ Background Removal Settings")
    bg_removal_method = st.radio(
        "Choose Background Removal Method",
        options=["auto", "remove.bg API", "rembg (free ML-based)"],
        index=0,
        help="""
        • **auto**: Smart selection - Uses remove.bg if API key provided, otherwise free rembg
        • **remove.bg API**: Professional service with high accuracy (requires API key above)
        • **rembg**: Free open-source ML models running locally (no API needed!)
        """
    )

    # Store the selection for processing
    if bg_removal_method == "rembg (free ML-based)":
        os.environ["BACKGROUND_REMOVAL_METHOD"] = "rembg"
        st.info("✅ Using free rembg ML model - no API key needed!")
    elif bg_removal_method == "remove.bg API":
        os.environ["BACKGROUND_REMOVAL_METHOD"] = "remove.bg"
        if not st.session_state.api_keys.get('removebg'):
            st.warning("⚠️ remove.bg API selected but no API key provided above")
    else:
        os.environ["BACKGROUND_REMOVAL_METHOD"] = "auto"
        if st.session_state.api_keys.get('removebg'):
            st.success("✅ Auto mode: Will use remove.bg API")
        else:
            st.info("ℹ️ Auto mode: Will use free rembg (no API key detected)")

    # Show rembg model selection when rembg is selected
    if bg_removal_method == "rembg (free ML-based)":
        col1, col2 = st.columns(2)

        with col1:
            rembg_model = st.selectbox(
                "rembg Model",
                options=[
                    "bria-rmbg",
                    "u2net",
                    "u2netp",
                    "u2net_human_seg",
                    "u2net_cloth_seg",
                    "silueta",
                    "isnet-general-use",
                    "isnet-anime",
                    "sam",
                    "birefnet-general",
                    "birefnet-general-lite",
                    "birefnet-portrait",
                    "birefnet-dis",
                    "birefnet-hrsod",
                    "birefnet-cod",
                    "birefnet-massive",
                    "ben2-base"
                ],
                index=0,
                help="""
                **Product Photography:**
                • **bria-rmbg**: Best for products (recommended)
                • **birefnet-general**: High quality, latest architecture
                • **isnet-general-use**: High accuracy general purpose

                **General Purpose:**
                • **u2net**: Default model, good balance
                • **u2netp**: Lightweight (~4MB), faster but lower quality
                • **silueta**: Smaller size (43MB), good balance

                **Human/Portrait:**
                • **u2net_human_seg**: Better for people, hair, clothing
                • **birefnet-portrait**: Optimized for portraits
                • **u2net_cloth_seg**: Clothing segmentation

                **Specialized:**
                • **isnet-anime**: Anime characters
                • **sam**: Interactive segmentation with prompts
                • **birefnet-hrsod**: High-res salient objects
                • **birefnet-massive**: Trained on massive dataset
                """
            )
            os.environ["REMBG_MODEL"] = rembg_model

        with col2:
            use_alpha_matting = st.checkbox(
                "Enable Alpha Matting",
                value=False,
                help="Improves edge quality but slower processing"
            )
            os.environ["REMBG_ALPHA_MATTING"] = "true" if use_alpha_matting else "false"

    # Quality Settings
    st.subheader("🎨 Quality Settings")
    quality_preset = st.selectbox(
        "Quality Preset",
        options=['ultra', 'maximum', 'high', 'balanced', 'web'],
        index=0,
        help="Choose output quality. 'Ultra' (default) provides excellent quality with reasonable file sizes. 'Maximum' uses lossless compression for absolute best quality."
    )

    # Apply quality preset to environment
    os.environ['QUALITY_PRESET'] = quality_preset

    # Show quality details
    quality_details = {
        'maximum': '100% lossless, largest files',
        'ultra': '98% quality, near-lossless',
        'high': '95% quality, excellent',
        'balanced': '92% quality, good',
        'web': '85% quality, optimized for web'
    }
    st.caption(f"💡 {quality_details.get(quality_preset, '')}")

    st.subheader("Processing Options")
    use_imagemagick = st.checkbox("Use ImageMagick Optimization", value=True,
                                 help="Traditional image processing for sharpening, color correction, and optimization. Disable to skip.")
    use_gemini = st.checkbox("Use Gemini AI Enhancement", value=False, 
                            help="Enable for AI-powered editing (lower resolution). Disable for traditional high-resolution processing.")
    
    # AI Upscaling option (only shows when using regular Gemini)
    use_ai_upscaling = False
    if use_gemini:
        use_ai_upscaling = st.checkbox(
            "🚀 Use Google AI Upscaling (Experimental)", 
            value=False,
            help="Experimental: Use Google AI to upscale images. Enhanced Lanczos (default) often provides better quality for product photos."
        )
    
    use_chunked_gemini = st.checkbox("Use Chunked Gemini (High-Res AI) 🆕", value=False,
                            help="Process high-resolution images through Gemini by intelligent chunking. Maintains full resolution with AI editing.")
    
    # Show 4K mode option when chunked Gemini is selected
    use_4k_mode = False
    if use_chunked_gemini:
        use_4k_mode = st.checkbox("Enable 4K Mode for Large Images", value=True,
                                 help="For images over 12MP, process at 4K resolution for faster results. Perfect for web/screen viewing.")
        use_gemini = False  # Disable regular Gemini if chunked is selected
    
    # Targeted Enhancement option (only shows when not using chunked or regular Gemini and ImageMagick is enabled)
    use_targeted_enhancement = False
    if not use_gemini and not use_chunked_gemini and use_imagemagick:
        use_targeted_enhancement = st.checkbox(
            "🎯 Targeted Gemini Enhancement", 
            value=False,
            help="After ImageMagick optimization, identify and enhance specific areas (chrome, textures, details) with Gemini AI"
        )
    
    # Defect Repair option (NEW)
    use_defect_repair = st.checkbox(
        "🔧 Auto Defect Repair (Experimental)", 
        value=False,
        help="Automatically detect and repair dust, scratches, and hot pixels using G'MIC and OpenCV"
    )
    
    # Defect repair sensitivity slider (only show when repair is enabled)
    defect_sensitivity = 50  # Default
    if use_defect_repair:
        defect_sensitivity = st.slider(
            "Defect Detection Sensitivity",
            min_value=10,
            max_value=90,
            value=50,
            step=10,
            help="Lower = only obvious defects, Higher = more aggressive detection"
        )

    remove_background = st.checkbox("Remove Background", value=True)

    auto_trim = st.checkbox(
        "Auto-Trim Excess Whitespace",
        value=False,
        help="Automatically remove excess whitespace/borders from the image. Uncheck if you want to preserve the original framing."
    )

    st.subheader("🔄 Quality Control")
    skip_retries = st.checkbox(
        "Skip Quality Retries (Faster Processing)",
        value=False,
        help="Disable automatic retries for faster results. Uncheck for best quality (may retry 2-3 times)."
    )
    
    # ImageMagick Base Configuration Section
    st.subheader("🎛️ ImageMagick Base Settings")
    
    # Initialize ImageMagick settings in session state if not present
    if 'imagemagick_settings' not in st.session_state:
        # Try to load from localStorage first
        stored_settings = localS.getItem('imagemagick_settings')
        if stored_settings:
            try:
                import json
                loaded_settings = json.loads(stored_settings)
                # Ensure all required keys exist with defaults
                default_settings = {
                    'gamma': 1.0,
                    'brightness': 0,
                    'contrast': 2,
                    'saturation': 108,
                    'sharpness': "1.0x0.5",
                    'highlights': -5,
                    'shadows': 3,
                    'quality': 95,
                    'vibrance': 0,
                    'preset': 'Default'
                }
                # Merge loaded settings with defaults (loaded settings take precedence)
                for key, default_value in default_settings.items():
                    if key not in loaded_settings:
                        loaded_settings[key] = default_value
                st.session_state.imagemagick_settings = loaded_settings
            except:
                # Use defaults if loading fails
                st.session_state.imagemagick_settings = {
                    'gamma': 1.0,
                    'brightness': 0,
                    'contrast': 2,
                    'saturation': 108,
                    'sharpness': "1.0x0.5",
                    'highlights': -5,
                    'shadows': 3,
                    'quality': 95,
                    'vibrance': 0,
                    'preset': 'Default'
                }
        else:
            st.session_state.imagemagick_settings = {
                'gamma': 1.0,
                'brightness': 0,
                'contrast': 2,
                'saturation': 108,
                'sharpness': "1.0x0.5",
                'highlights': -5,
                'shadows': 3,
                'quality': 95,
                'vibrance': 0,
                'preset': 'Default'
            }
    
    # Preset configurations
    presets = {
        'Default': {'gamma': 1.0, 'brightness': 0, 'contrast': 2, 'saturation': 108, 'highlights': -5, 'shadows': 3},
        'Natural Product': {'gamma': 1.02, 'brightness': 0, 'contrast': 1, 'saturation': 105, 'highlights': -3, 'shadows': 2},
        'Vibrant E-commerce': {'gamma': 1.05, 'brightness': 2, 'contrast': 3, 'saturation': 115, 'highlights': -8, 'shadows': 5},
        'Chrome/Metal': {'gamma': 0.95, 'brightness': -2, 'contrast': 4, 'saturation': 102, 'highlights': -12, 'shadows': 3},
        'Soft/Matte': {'gamma': 1.0, 'brightness': 1, 'contrast': 0, 'saturation': 106, 'highlights': -2, 'shadows': 4},
        'High-key White': {'gamma': 1.08, 'brightness': 3, 'contrast': -1, 'saturation': 103, 'highlights': 0, 'shadows': 8},
        'Custom': None  # Indicates custom settings
    }
    
    # Preset selector
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_preset = st.selectbox(
            "Preset Configuration",
            list(presets.keys()),
            index=list(presets.keys()).index(st.session_state.imagemagick_settings.get('preset', 'Default')),
            help="Choose a preset or select Custom to adjust manually"
        )
    
    with col2:
        if st.button("🔄 Reset to Default"):
            st.session_state.imagemagick_settings = presets['Default'].copy()
            st.session_state.imagemagick_settings['preset'] = 'Default'
            st.rerun()
    
    # Apply preset if changed
    if selected_preset != st.session_state.imagemagick_settings.get('preset', 'Default'):
        if selected_preset != 'Custom' and presets[selected_preset]:
            st.session_state.imagemagick_settings.update(presets[selected_preset])
            st.session_state.imagemagick_settings['preset'] = selected_preset
            # Save to localStorage
            import json
            localS.setItem('imagemagick_settings', json.dumps(st.session_state.imagemagick_settings))
            st.rerun()
    
    # Show/hide advanced settings
    show_advanced = st.checkbox("🎚️ Show Advanced Settings", value=(selected_preset == 'Custom'))
    
    if show_advanced:
        st.markdown("#### Fine-tune Parameters")
        
        # Create three columns for parameters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.session_state.imagemagick_settings['gamma'] = st.slider(
                "Gamma",
                min_value=0.5, max_value=2.0, value=st.session_state.imagemagick_settings['gamma'],
                step=0.01, help="Overall brightness curve (1.0 = neutral)"
            )
            
            st.session_state.imagemagick_settings['brightness'] = st.slider(
                "Brightness",
                min_value=-20, max_value=20, value=st.session_state.imagemagick_settings['brightness'],
                step=1, help="Linear brightness adjustment"
            )
            
            st.session_state.imagemagick_settings['contrast'] = st.slider(
                "Contrast",
                min_value=-20, max_value=20, value=st.session_state.imagemagick_settings['contrast'],
                step=1, help="Contrast adjustment"
            )
        
        with col2:
            st.session_state.imagemagick_settings['saturation'] = st.slider(
                "Saturation",
                min_value=50, max_value=200, value=st.session_state.imagemagick_settings['saturation'],
                step=1, help="Color saturation (100 = neutral)"
            )
            
            st.session_state.imagemagick_settings['vibrance'] = st.slider(
                "Vibrance",
                min_value=-100, max_value=100, value=st.session_state.imagemagick_settings['vibrance'],
                step=5, help="Selective saturation for less saturated colors"
            )
            
            st.session_state.imagemagick_settings['quality'] = st.slider(
                "Output Quality",
                min_value=70, max_value=100, value=st.session_state.imagemagick_settings.get('quality', 95),
                step=5, help="JPEG/WebP compression quality"
            )
        
        with col3:
            st.session_state.imagemagick_settings['highlights'] = st.slider(
                "Highlights",
                min_value=-30, max_value=5, value=st.session_state.imagemagick_settings['highlights'],
                step=1, help="Highlight recovery (negative = darken)"
            )
            
            st.session_state.imagemagick_settings['shadows'] = st.slider(
                "Shadows",
                min_value=-5, max_value=20, value=st.session_state.imagemagick_settings['shadows'],
                step=1, help="Shadow lifting (positive = brighten)"
            )
            
            # Sharpness as text input (it's a string like "1.0x0.5")
            sharpness_input = st.text_input(
                "Sharpness (RxS)",
                value=st.session_state.imagemagick_settings.get('sharpness', '1.0x0.5'),
                help="Unsharp mask parameters (e.g., 1.0x0.5)"
            )
            if sharpness_input:
                st.session_state.imagemagick_settings['sharpness'] = sharpness_input
        
        # Mark as custom if user changed any value
        st.session_state.imagemagick_settings['preset'] = 'Custom'
        
        # Save to localStorage whenever settings change
        import json
        localS.setItem('imagemagick_settings', json.dumps(st.session_state.imagemagick_settings))
        
        # Show the resulting ImageMagick command
        with st.expander("🔧 View Generated ImageMagick Command"):
            # Build the command string
            cmd_parts = []
            
            gamma = st.session_state.imagemagick_settings['gamma']
            if gamma != 1.0:
                cmd_parts.append(f"-gamma {gamma}")
            
            brightness = st.session_state.imagemagick_settings['brightness']
            contrast = st.session_state.imagemagick_settings['contrast']
            if brightness != 0 or contrast != 0:
                cmd_parts.append(f"-brightness-contrast {brightness}x{contrast}")
            
            highlights = st.session_state.imagemagick_settings['highlights']
            shadows = st.session_state.imagemagick_settings['shadows']
            if highlights != 0 or shadows != 0:
                black_point = max(0, shadows)
                white_point = min(100, 100 + highlights)
                if black_point != 0 or white_point != 100:
                    cmd_parts.append(f"-level {black_point}%,{white_point}%")
            
            saturation = st.session_state.imagemagick_settings['saturation']
            if saturation != 100:
                cmd_parts.append(f"-modulate 100,{saturation},100")
            
            vibrance = st.session_state.imagemagick_settings['vibrance']
            if vibrance != 0:
                if vibrance > 0:
                    cmd_parts.append(f"-colorspace HSL -channel G -sigmoidal-contrast {vibrance/10},50% +channel -colorspace sRGB")
                else:
                    cmd_parts.append(f"-colorspace HSL -channel G +sigmoidal-contrast {abs(vibrance)/10},50% +channel -colorspace sRGB")
            
            sharpness = st.session_state.imagemagick_settings.get('sharpness', '1.0x0.5')
            if sharpness:
                cmd_parts.append(f"-unsharp {sharpness}")
            
            quality = st.session_state.imagemagick_settings.get('quality', 95)
            cmd_parts.append(f"-quality {quality}")
            
            command = " ".join(cmd_parts) if cmd_parts else "(no adjustments)"
            st.code(command, language="bash")
            st.caption("💡 This is the base command. Claude will add additional adjustments based on image analysis.")
    
    # Apply ImageMagick settings to environment with defaults for missing keys
    import os
    settings = st.session_state.imagemagick_settings
    os.environ['IMAGEMAGICK_GAMMA'] = str(settings.get('gamma', 1.0))
    os.environ['IMAGEMAGICK_BRIGHTNESS'] = str(settings.get('brightness', 0))
    os.environ['IMAGEMAGICK_CONTRAST'] = str(settings.get('contrast', 2))
    os.environ['IMAGEMAGICK_SATURATION'] = str(settings.get('saturation', 108))
    os.environ['IMAGEMAGICK_VIBRANCE'] = str(settings.get('vibrance', 0))
    os.environ['IMAGEMAGICK_HIGHLIGHTS'] = str(settings.get('highlights', -5))
    os.environ['IMAGEMAGICK_SHADOWS'] = str(settings.get('shadows', 3))
    os.environ['IMAGEMAGICK_SHARPNESS'] = settings.get('sharpness', '1.0x0.5')
    os.environ['IMAGEMAGICK_QUALITY'] = str(settings.get('quality', 95))
    
    st.subheader("📷 Lens Corrections")
    
    # Add checkbox to enable/disable lens corrections
    apply_lens_correction = st.checkbox(
        "Apply Lens Corrections", 
        value=False,
        help="Enable automatic lens corrections for distortion and vignetting. Disable if corrections are warping your image."
    )
    
    lens_options = get_lens_options()
    selected_lens = st.selectbox(
        "Select lens used (or auto-detect):",
        lens_options,
        index=len(lens_options) - 1,  # Default to auto-detect
        help="Select your Sony lens for automatic corrections like Lightroom",
        disabled=not apply_lens_correction  # Disable selector if corrections are off
    )
    
    # Show focal length selector for zoom lenses
    focal_length = None
    if apply_lens_correction and selected_lens and "mm F" in selected_lens and "-" in selected_lens:
        # It's a zoom lens, show focal length options
        focal_options = get_focal_length_options(selected_lens)
        if focal_options:
            focal_length = st.select_slider(
                "Focal length used:",
                options=focal_options,
                value=focal_options[len(focal_options)//2],  # Default to middle
                disabled=not apply_lens_correction
            )
    
    # Base ImageMagick Configuration Sliders
    with st.expander("🎛️ ImageMagick Base Configuration (Advanced)", expanded=False):
        st.markdown("Adjust the base settings for ImageMagick processing. These are the starting values before AI adjustments.")
        
        # Show live preview if image is uploaded
        if st.session_state.current_uploaded_file is not None and PREVIEW_AVAILABLE:
            preview_col, sliders_col = st.columns([1, 1])
            
            with preview_col:
                st.markdown("### Live Preview")
                preview_placeholder = st.empty()
        else:
            sliders_col = st.container()
            preview_placeholder = None
        
        with sliders_col if st.session_state.current_uploaded_file else st.container():
            col1_config, col2_config = st.columns(2)
        
            with col1_config:
                base_gamma = st.slider(
                    "Gamma",
                    min_value=0.8,
                    max_value=1.2,
                    value=1.0,
                    step=0.01,
                    key="gamma_slider",
                    help="Gamma correction (1.0 = neutral)"
                )
                
                base_brightness = st.slider(
                    "Brightness",
                    min_value=-10,
                    max_value=10,
                    value=0,
                    step=1,
                    key="brightness_slider",
                    help="Brightness adjustment"
                )
                
                base_contrast = st.slider(
                    "Contrast",
                    min_value=-10,
                    max_value=10,
                    value=2,  # Darktable-inspired default
                    step=1,
                    key="contrast_slider",
                    help="Contrast adjustment (2 = slight boost)"
                )
                
                base_saturation = st.slider(
                    "Saturation",
                    min_value=90,
                    max_value=120,
                    value=108,  # Darktable-inspired default
                    step=1,
                    key="saturation_slider",
                    help="Color saturation (100 = neutral)"
                )
            
            with col2_config:
                base_highlights = st.slider(
                    "Highlights",
                    min_value=-20,
                    max_value=20,
                    value=-5,  # Darktable-inspired default
                    step=1,
                    key="highlights_slider",
                    help="Highlight recovery (negative = recover)"
                )
                
                base_shadows = st.slider(
                    "Shadows",
                    min_value=-10,
                    max_value=10,
                    value=3,  # Darktable-inspired default
                    step=1,
                    key="shadows_slider",
                    help="Shadow adjustment (positive = lift)"
                )
                
                base_sharpness_radius = st.slider(
                    "Sharpness Radius",
                    min_value=0.5,
                    max_value=2.0,
                    value=1.0,  # Darktable-inspired default
                    step=0.1,
                    key="sharp_radius_slider",
                    help="Unsharp mask radius"
                )
                
                base_sharpness_sigma = st.slider(
                    "Sharpness Sigma",
                    min_value=0.3,
                    max_value=1.0,
                    value=0.5,  # Darktable-inspired default
                    step=0.1,
                    key="sharp_sigma_slider",
                    help="Unsharp mask sigma"
                )
        
            # Reset to defaults button
            if st.button("Reset to Darktable Defaults", type="secondary"):
                st.rerun()
        
        # Generate live preview if image is uploaded
        if st.session_state.current_uploaded_file is not None and preview_placeholder is not None and PREVIEW_AVAILABLE:
            try:
                # Save uploaded file temporarily for preview
                uploaded_file_data = st.session_state.current_uploaded_file
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file_data['name']).suffix) as tmp_file:
                    tmp_file.write(uploaded_file_data['data'])
                    temp_path = tmp_file.name
                
                # Generate preview with current slider values
                preview_bytes = generate_preview_from_sliders(
                    source_image_path=temp_path,
                    gamma=base_gamma,
                    brightness=base_brightness,
                    contrast=base_contrast,
                    saturation=base_saturation,
                    highlights=base_highlights,
                    shadows=base_shadows,
                    sharpness_radius=base_sharpness_radius,
                    sharpness_sigma=base_sharpness_sigma,
                    max_size=(400, 400)  # Smaller for faster updates
                )
                
                # Display preview
                with preview_placeholder.container():
                    st.image(preview_bytes, caption="Preview (not full resolution)", width="stretch")
                    st.caption("⚡ Real-time preview of adjustments")
                
                # Clean up temp file
                os.unlink(temp_path)
            except Exception as e:
                with preview_placeholder.container():
                    st.warning(f"Preview unavailable: {str(e)}")
    
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
    "Choose Mode:",
    ["🖼️ Single Image", "📦 Batch Processing", "❓ Help & Guide"],
    horizontal=True,
    help="Single Image: Process one image | Batch: Process multiple images | Help: Learn how to use the app"
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
            type=['png', 'jpg', 'jpeg', 'webp', 'avif'],
            key="single_upload"
        )
        
        # Store uploaded file in session state for preview access
        if uploaded_file:
            st.session_state.current_uploaded_file = {
                'name': uploaded_file.name,
                'data': uploaded_file.getvalue()
            }
        else:
            st.session_state.current_uploaded_file = None
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Original Image", width="stretch")
            
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
            st.image(st.session_state.processed_image, caption="Enhanced Image", width="stretch")
            
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
                metrics = st.session_state.processing_metrics
                
                # Check if it's chunked mode with extended metrics
                if 'chunks_processed' in metrics:
                    # Chunked mode - show more metrics
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Quality", metrics['quality'])
                    with col_b:
                        st.metric("Chunks", metrics['chunks_processed'])
                    with col_c:
                        if 'mode' in metrics:
                            st.metric("Mode", metrics['mode'])
                        else:
                            st.metric("Strategy", metrics['strategy'])
                    
                    # Show resolution info if available
                    if metrics.get('original_resolution') != 'N/A':
                        col_d, col_e = st.columns(2)
                        with col_d:
                            orig_res = metrics['original_resolution']
                            if isinstance(orig_res, tuple):
                                st.metric("Original", f"{orig_res[0]}x{orig_res[1]}")
                            else:
                                st.metric("Original", orig_res)
                        with col_e:
                            final_res = metrics['final_resolution']
                            if isinstance(final_res, tuple):
                                st.metric("Final", f"{final_res[0]}x{final_res[1]}")
                            else:
                                st.metric("Final", final_res)
                else:
                    # Standard mode - show basic metrics
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Quality Score", metrics['quality'])
                    with col_b:
                        st.metric("Strategy Used", metrics['strategy'])
        
        if uploaded_file and process_button:
            # Get keys from session state (saved via form)
            final_anthropic = st.session_state.api_keys.get('anthropic', '')
            final_gemini = st.session_state.api_keys.get('gemini', '')
            final_removebg = st.session_state.api_keys.get('removebg', '')

            # Debug logging
            print(f"🔍 STREAMLIT DEBUG: Processing started")
            print(f"   Anthropic key in session: {final_anthropic[:8] if final_anthropic else 'EMPTY'}...")
            print(f"   Gemini key in session: {final_gemini[:8] if final_gemini else 'EMPTY'}...")
            print(f"   RemoveBG key in session: {final_removebg[:8] if final_removebg else 'EMPTY'}...")

            if not final_anthropic:
                st.error("⚠️ Please enter your Anthropic API key in the sidebar and click 'Save Keys'")
            elif use_gemini and not final_gemini:
                st.error("⚠️ Please enter your Gemini API key in the sidebar and click 'Save Keys'")
            else:
                # Prepare API keys dict
                api_keys = {
                    'anthropic': final_anthropic,
                    'gemini': final_gemini,
                    'removebg': final_removebg
                }
                print(f"✅ Created api_keys dict with {len([k for k, v in api_keys.items() if v])} non-empty keys")

                # Configure LangSmith tracing
                # Check if LANGSMITH_API_KEY exists in environment or Streamlit secrets
                try:
                    langsmith_key = os.getenv("LANGSMITH_API_KEY") or st.secrets.get("LANGSMITH_API_KEY", None)
                    if langsmith_key:
                        os.environ["LANGSMITH_API_KEY"] = langsmith_key
                        os.environ["LANGSMITH_TRACING"] = "true"
                        os.environ["LANGSMITH_PROJECT"] = "langgraph-photo-editor"
                        print(f"✅ LangSmith tracing enabled: {langsmith_key[:20]}...")
                    else:
                        print("ℹ️ LangSmith tracing not configured (no API key found)")
                except Exception as e:
                    print(f"⚠️ LangSmith configuration failed: {e}")

                # Configure retry behavior
                os.environ["SKIP_RETRIES"] = "true" if skip_retries else "false"

                # Background removal settings are already configured in sidebar (lines 182-254)

                with st.spinner("🔄 Processing your image..."):
                    try:
                        with tempfile.TemporaryDirectory() as temp_dir:
                            # Handle AVIF conversion if needed
                            if Path(uploaded_file.name).suffix.lower() == '.avif':
                                # Convert AVIF to WebP
                                from PIL import Image as PILImage
                                import io
                                
                                img = PILImage.open(uploaded_file)
                                webp_buffer = io.BytesIO()
                                img.save(webp_buffer, 'WEBP', quality=95, method=6)
                                webp_buffer.seek(0)
                                
                                # Save as WebP
                                input_path = Path(temp_dir) / f"{Path(uploaded_file.name).stem}.webp"
                                with open(input_path, "wb") as f:
                                    f.write(webp_buffer.getvalue())
                                st.info("🔄 Converted AVIF to WebP for processing")
                            else:
                                input_path = Path(temp_dir) / uploaded_file.name
                                with open(input_path, "wb") as f:
                                    f.write(uploaded_file.getbuffer())
                            
                            # Apply lens corrections first if enabled and applicable
                            if apply_lens_correction:
                                corrected_path = str(Path(temp_dir) / f"corrected_{uploaded_file.name}")
                                lens_result = apply_lens_corrections(
                                    str(input_path),
                                    corrected_path,
                                    selected_lens=selected_lens if selected_lens != "None (Auto-detect from EXIF)" else None,
                                    focal_length=float(focal_length.replace('mm', '')) if focal_length else None
                                )
                            else:
                                # Skip lens corrections
                                lens_result = {'corrections_applied': False, 'reason': 'Lens corrections disabled by user'}
                                corrected_path = str(input_path)
                            
                            # Use corrected image if corrections were applied
                            if lens_result.get('corrections_applied'):
                                st.info(f"📷 Applied lens corrections: {lens_result.get('message', '')}")
                                process_path = corrected_path
                            elif lens_result.get('lens_used'):
                                # Lens was detected but corrections couldn't be applied
                                if lens_result.get('detected_from_exif'):
                                    st.info(f"📷 Auto-detected lens: {lens_result.get('lens_used')} (from EXIF)")
                                st.warning(f"⚠️ {lens_result.get('reason', 'Corrections not applied')}")
                                process_path = str(input_path)
                            else:
                                # No lens detected
                                if selected_lens == "None (Auto-detect from EXIF)":
                                    st.info("📷 No lens data found in EXIF, proceeding without lens corrections")
                                process_path = str(input_path)
                            
                            # Check which processing mode to use
                            if use_chunked_gemini:
                                # Use chunked Gemini pipeline for high-res AI processing
                                from src.chunked_gemini_workflow import chunked_gemini_pipeline
                                result = asyncio.run(chunked_gemini_pipeline(
                                    image_path=process_path,
                                    custom_instructions=instructions,
                                    output_dir=temp_dir,
                                    target_4k=use_4k_mode,
                                    remove_background=remove_background
                                ))
                            else:
                                # Add processing preferences to instructions
                                final_instructions = instructions
                                if not use_gemini:
                                    final_instructions += " Skip Gemini."
                                if not use_imagemagick:
                                    final_instructions += " Skip ImageMagick."
                                
                                # Set targeted enhancement flag if enabled
                                if use_targeted_enhancement:
                                    os.environ["USE_TARGETED_ENHANCEMENT"] = "true"
                                else:
                                    os.environ["USE_TARGETED_ENHANCEMENT"] = "false"
                                
                                # Set AI upscaling flag
                                if use_ai_upscaling:
                                    os.environ["USE_AI_UPSCALING"] = "true"
                                else:
                                    os.environ["USE_AI_UPSCALING"] = "false"
                                
                                # Set lens correction preference
                                if not apply_lens_correction:
                                    os.environ["SKIP_LENS_CORRECTION"] = "true"
                                else:
                                    os.environ["SKIP_LENS_CORRECTION"] = "false"
                                
                                # Set ImageMagick preference
                                if not use_imagemagick:
                                    os.environ["SKIP_IMAGEMAGICK"] = "true"
                                else:
                                    os.environ["SKIP_IMAGEMAGICK"] = "false"
                                
                                # Set defect repair preference (NEW)
                                if use_defect_repair:
                                    os.environ["SKIP_REPAIR"] = "false"
                                    os.environ["DEFECT_SENSITIVITY"] = str(defect_sensitivity)
                                else:
                                    os.environ["SKIP_REPAIR"] = "true"
                                
                                # Set background removal preference
                                if not remove_background:
                                    os.environ["SKIP_BACKGROUND_REMOVAL"] = "true"
                                else:
                                    os.environ["SKIP_BACKGROUND_REMOVAL"] = "false"

                                # Set auto-trim preference
                                os.environ["IMAGEMAGICK_TRIM"] = "true" if auto_trim else "false"

                                # Set defect repair flag
                                if use_defect_repair:
                                    os.environ["USE_DEFECT_REPAIR"] = "true"
                                else:
                                    os.environ.pop("USE_DEFECT_REPAIR", None)
                                
                                # Build custom base config from sliders
                                # Check if we have the slider variables available
                                if 'base_gamma' in locals():
                                    print(f"🔍 DEBUG: base_gamma={base_gamma}, base_brightness={base_brightness}, base_contrast={base_contrast}, base_saturation={base_saturation}")
                                    custom_base_parts = []
                                    
                                    # IMPORTANT: Order matters in ImageMagick!
                                    
                                    # 1. Gamma adjustment first (affects overall brightness)
                                    if base_gamma != 1.0:
                                        custom_base_parts.append(f"-gamma {base_gamma}")
                                        print(f"🔍 Added gamma: {base_gamma}")
                                    
                                    # 2. Brightness/Contrast adjustments
                                    if base_brightness != 0 or base_contrast != 0:
                                        custom_base_parts.append(f"-brightness-contrast {base_brightness}x{base_contrast}")
                                    
                                    # 3. Highlight/Shadow adjustment using -level
                                    if base_highlights != 0 or base_shadows != 0:
                                        black_point = max(0, base_shadows)
                                        white_point = min(100, 100 + base_highlights)
                                        if black_point != 0 or white_point != 100:
                                            custom_base_parts.append(f"-level {black_point}%,{white_point}%")
                                    
                                    # 4. Saturation
                                    if base_saturation != 100:
                                        custom_base_parts.append(f"-modulate 100,{base_saturation},100")
                                    
                                    # 5. Sharpening
                                    custom_base_parts.append(f"-unsharp {base_sharpness_radius}x{base_sharpness_sigma}")
                                    
                                    # 6. Quality
                                    custom_base_parts.append("-quality 95")
                                    
                                    # Set the custom base config
                                    custom_config = " ".join(custom_base_parts)
                                    os.environ["IMAGEMAGICK_BASE_CONFIG"] = custom_config
                                    print(f"🎛️ Set custom ImageMagick config: {custom_config}")
                                
                                # The workflow already handles Pregel invocation internally
                                result = asyncio.run(process_single_image_enhanced(
                                    image_path=process_path,
                                    custom_instructions=final_instructions,
                                    output_dir=temp_dir,
                                    api_keys=api_keys
                                ))
                            
                            if result.get("final_image"):
                                output_path = result.get("final_image")
                                print(f"📸 DEBUG: Result final_image path: {output_path}")
                                print(f"📸 DEBUG: Path exists: {Path(output_path).exists() if output_path else 'None'}")
                                
                                if output_path and Path(output_path).exists():
                                    # Check file size and type
                                    file_size = os.path.getsize(output_path)
                                    print(f"📸 DEBUG: Loading image from: {output_path} ({file_size} bytes)")
                                    
                                    result_image = Image.open(output_path)
                                    width, height = result_image.size
                                    print(f"📸 DEBUG: Image dimensions: {width}x{height}")
                                    
                                    st.session_state.processed_image = result_image
                                    with open(output_path, "rb") as f:
                                        st.session_state.processed_image_data = f.read()
                                    st.session_state.processed_filename = f"enhanced_{uploaded_file.name}"
                                    
                                    # Debug: Check if this is a Gemini-edited image
                                    if "gemini-edited" in output_path:
                                        print(f"✅ DEBUG: This is a Gemini-edited image!")
                                    else:
                                        print(f"⚠️ DEBUG: Not a Gemini-edited image path")
                                    
                                    quality = result.get('final_quality', result.get('quality_score', 'N/A'))
                                    if quality != 'N/A':
                                        quality_display = f"{quality}/10"
                                    else:
                                        quality_display = quality
                                    strategy = result.get('strategy', 'Enhanced AI Pipeline')
                                    
                                    # Add resolution info for chunked mode
                                    if use_chunked_gemini:
                                        metrics = {
                                            'quality': quality_display,
                                            'strategy': 'Chunked Gemini AI',
                                            'chunks_processed': f"{result.get('chunks_processed', 'N/A')}/{result.get('total_chunks', 'N/A')}",
                                            'original_resolution': result.get('original_resolution', 'N/A'),
                                            'final_resolution': result.get('final_resolution', 'N/A')
                                        }
                                        if result.get('used_4k_mode'):
                                            metrics['mode'] = '4K Optimized'
                                    else:
                                        metrics = {
                                            'quality': quality_display,
                                            'strategy': strategy
                                        }
                                        if result.get('targeted_enhancement_used'):
                                            metrics['targeted_areas'] = '🎯 Enhanced'
                                    
                                    st.session_state.processing_metrics = metrics
                                    
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
elif mode == "📦 Batch Processing":
    st.header("📤 Upload Multiple Images")
    
    uploaded_files = st.file_uploader(
        "Choose images to process...",
        type=['png', 'jpg', 'jpeg', 'webp', 'avif'],
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
                st.image(image, caption=file.name[:20], width="stretch")
        
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
        
        # Batch processing options
        st.subheader("⚙️ Processing Options")
        col1b, col2b = st.columns(2)
        
        with col1b:
            batch_use_imagemagick = st.checkbox("Use ImageMagick Optimization", value=True, key="batch_imagemagick",
                                         help="Traditional image processing for sharpening, color correction, and optimization.")
            batch_use_gemini = st.checkbox("Use Gemini AI Enhancement", value=False, key="batch_gemini",
                                    help="Enable for AI-powered editing (lower resolution).")
            batch_use_chunked_gemini = st.checkbox("Use Chunked Gemini (High-Res AI)", value=False, key="batch_chunked",
                                    help="Process high-resolution images through Gemini by intelligent chunking.")
        
        with col2b:
            batch_use_defect_repair = st.checkbox("Auto Dust & Scratch Repair 🧹", value=False, key="batch_defect",
                                    help="Automatically detect and remove dust spots, sensor debris, and scratches.")
            batch_remove_background = st.checkbox("Remove Background", value=True, key="batch_remove_bg")
            batch_auto_trim = st.checkbox(
                "Auto-Trim Excess Whitespace",
                value=False,
                key="batch_auto_trim",
                help="Automatically remove excess whitespace/borders from images. Uncheck to preserve original framing."
            )

            # Show background removal method selection when enabled
            batch_bg_method = "Use sidebar settings"  # Default value
            batch_rembg_model = "bria-rmbg"  # Default model
            if batch_remove_background:
                batch_bg_method = st.selectbox(
                    "Background Removal Method",
                    options=["Use sidebar settings", "auto", "remove.bg API", "rembg (free)"],
                    index=0,
                    key="batch_bg_method",
                    help="Use sidebar settings or override for this batch"
                )

                # Show model selection if rembg is chosen
                if batch_bg_method == "rembg (free)":
                    batch_rembg_model = st.selectbox(
                        "rembg Model for Batch",
                        options=[
                            "bria-rmbg",
                            "u2net",
                            "u2netp",
                            "u2net_human_seg",
                            "u2net_cloth_seg",
                            "silueta",
                            "isnet-general-use",
                            "isnet-anime",
                            "sam",
                            "birefnet-general",
                            "birefnet-general-lite",
                            "birefnet-portrait",
                            "birefnet-dis",
                            "birefnet-hrsod",
                            "birefnet-cod",
                            "birefnet-massive",
                            "ben2-base"
                        ],
                        index=0,
                        key="batch_rembg_model",
                        help="Select the rembg model for this batch"
                    )
            # Show 4K mode option when chunked Gemini is selected
            batch_use_4k_mode = False
            if batch_use_chunked_gemini:
                batch_use_4k_mode = st.checkbox("Enable 4K Mode", value=True, key="batch_4k",
                                         help="For images over 12MP, process at 4K resolution.")
                batch_use_gemini = False  # Disable regular Gemini if chunked is selected
            
            # Targeted Enhancement option
            batch_use_targeted = False
            if not batch_use_gemini and not batch_use_chunked_gemini and batch_use_imagemagick:
                batch_use_targeted = st.checkbox("🎯 Targeted Enhancement", value=False, key="batch_targeted",
                    help="Enhance specific areas with Gemini AI after ImageMagick")
            
            # Defect Repair option (NEW)
            batch_use_repair = st.checkbox(
                "🔧 Auto Defect Repair", 
                value=False, 
                key="batch_repair",
                help="Automatically detect and repair dust, scratches, and hot pixels"
            )
            
            # Batch defect sensitivity
            batch_defect_sensitivity = 50
            if batch_use_repair:
                batch_defect_sensitivity = st.slider(
                    "Defect Detection Sensitivity",
                    min_value=10,
                    max_value=90,
                    value=50,
                    step=10,
                    key="batch_sensitivity",
                    help="Lower = only obvious defects, Higher = more aggressive detection"
                )
        
        # Batch consistency option
        st.subheader("🎯 Consistency Options")
        use_batch_consistency = st.checkbox(
            "Enable Batch Consistency Mode",
            value=True,
            help="Analyze all images first to ensure consistent brightness, color, and enhancement levels across the entire batch. Prevents some images from being much brighter/darker than others."
        )
        
        if use_batch_consistency:
            st.info("📊 Batch consistency will analyze all images first to establish uniform processing parameters")

        # Quality control options
        st.subheader("🔄 Quality Control")
        skip_retries = st.checkbox(
            "Skip Quality Retries (Faster Batch Processing)",
            value=False,
            key="batch_skip_retries",
            help="Disable automatic retries for faster results. Uncheck for best quality (may retry 2-3 times per image)."
        )

        # Base ImageMagick Configuration for Batch
        with st.expander("🎛️ Batch ImageMagick Base Configuration (Advanced)", expanded=False):
            st.markdown("Set consistent base settings for the entire batch. These values will be used for all images.")
            
            batch_col1_config, batch_col2_config = st.columns(2)
            
            with batch_col1_config:
                batch_base_gamma = st.slider(
                    "Gamma",
                    min_value=0.8,
                    max_value=1.2,
                    value=1.0,
                    step=0.01,
                    key="batch_gamma",
                    help="Gamma correction (1.0 = neutral)"
                )
                
                batch_base_brightness = st.slider(
                    "Brightness",
                    min_value=-10,
                    max_value=10,
                    value=0,
                    step=1,
                    key="batch_brightness",
                    help="Brightness adjustment"
                )
                
                batch_base_contrast = st.slider(
                    "Contrast",
                    min_value=-10,
                    max_value=10,
                    value=2,
                    step=1,
                    key="batch_contrast",
                    help="Contrast adjustment"
                )
                
                batch_base_saturation = st.slider(
                    "Saturation",
                    min_value=90,
                    max_value=120,
                    value=108,
                    step=1,
                    key="batch_saturation",
                    help="Color saturation"
                )
            
            with batch_col2_config:
                batch_base_highlights = st.slider(
                    "Highlights",
                    min_value=-20,
                    max_value=20,
                    value=-5,
                    step=1,
                    key="batch_highlights",
                    help="Highlight recovery"
                )
                
                batch_base_shadows = st.slider(
                    "Shadows",
                    min_value=-10,
                    max_value=10,
                    value=3,
                    step=1,
                    key="batch_shadows",
                    help="Shadow adjustment"
                )
                
                batch_base_sharpness_radius = st.slider(
                    "Sharpness Radius",
                    min_value=0.5,
                    max_value=2.0,
                    value=1.0,
                    step=0.1,
                    key="batch_sharp_radius",
                    help="Unsharp mask radius"
                )
                
                batch_base_sharpness_sigma = st.slider(
                    "Sharpness Sigma",
                    min_value=0.3,
                    max_value=1.0,
                    value=0.5,
                    step=0.1,
                    key="batch_sharp_sigma",
                    help="Unsharp mask sigma"
                )
            
            if st.button("Reset Batch to Darktable Defaults", type="secondary", key="batch_reset"):
                st.rerun()
        
        st.subheader("✏️ Batch Instructions")
        batch_instructions = st.text_area(
            "Enter editing instructions (applied to all images):",
            value="Enhance the product photo for e-commerce. Make it more vibrant and professional.",
            height=100
        )
        
        process_batch_button = st.button("🚀 Process All Images", type="primary", use_container_width=True)

        if process_batch_button:
            # Get keys from session state (same as single image mode)
            final_anthropic = st.session_state.api_keys.get('anthropic', '')
            final_gemini = st.session_state.api_keys.get('gemini', '')
            final_removebg = st.session_state.api_keys.get('removebg', '')

            if not final_anthropic:
                st.error("⚠️ Please enter your Anthropic API key in the sidebar and click 'Save Keys'")
            elif (batch_use_gemini or batch_use_chunked_gemini) and not final_gemini:
                st.error("⚠️ Please enter your Gemini API key in the sidebar and click 'Save Keys'")
            else:
                # Prepare API keys dict
                api_keys = {
                    'anthropic': final_anthropic,
                    'gemini': final_gemini,
                    'removebg': final_removebg
                }

                # Configure LangSmith tracing
                # Check if LANGSMITH_API_KEY exists in environment or Streamlit secrets
                try:
                    langsmith_key = os.getenv("LANGSMITH_API_KEY") or st.secrets.get("LANGSMITH_API_KEY", None)
                    if langsmith_key:
                        os.environ["LANGSMITH_API_KEY"] = langsmith_key
                        os.environ["LANGSMITH_TRACING"] = "true"
                        os.environ["LANGSMITH_PROJECT"] = "langgraph-photo-editor"
                        print(f"✅ LangSmith tracing enabled (batch): {langsmith_key[:20]}...")
                    else:
                        print("ℹ️ LangSmith tracing not configured for batch (no API key found)")
                except Exception as e:
                    print(f"⚠️ LangSmith configuration failed (batch): {e}")

                # Configure retry behavior
                os.environ["SKIP_RETRIES"] = "true" if skip_retries else "false"

                # Configure background removal method for batch
                if batch_remove_background:
                    if batch_bg_method == "Auto (Smart Selection)":
                        os.environ["BACKGROUND_REMOVAL_METHOD"] = "auto"
                        os.environ["REMBG_MODEL"] = batch_rembg_model
                        os.environ["REMBG_ALPHA_MATTING"] = "true" if batch_use_alpha_matting else "false"
                    elif batch_bg_method == "rembg (Local)":
                        os.environ["BACKGROUND_REMOVAL_METHOD"] = "rembg"
                        os.environ["REMBG_MODEL"] = batch_rembg_model
                        os.environ["REMBG_ALPHA_MATTING"] = "true" if batch_use_alpha_matting else "false"
                    else:  # remove.bg (API)
                        os.environ["BACKGROUND_REMOVAL_METHOD"] = "remove.bg"

                st.markdown("---")
                st.header("⚙️ Processing Images")
                
                progress_bar = st.progress(0, text="Starting batch processing...")
                status_text = st.empty()
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    results = []
                    
                    async def process_image_async(file, idx, total):
                        try:
                            # Handle AVIF conversion if needed
                            if Path(file.name).suffix.lower() == '.avif':
                                # Convert AVIF to WebP
                                from PIL import Image as PILImage
                                import io
                                
                                img = PILImage.open(file)
                                webp_buffer = io.BytesIO()
                                img.save(webp_buffer, 'WEBP', quality=95, method=6)
                                webp_buffer.seek(0)
                                
                                # Save as WebP
                                input_path = Path(temp_dir) / f"input_{idx}_{Path(file.name).stem}.webp"
                                with open(input_path, "wb") as f:
                                    f.write(webp_buffer.getvalue())
                            else:
                                input_path = Path(temp_dir) / f"input_{idx}_{file.name}"
                                with open(input_path, "wb") as f:
                                    f.write(file.getbuffer())
                            
                            status_text.text(f"Processing {file.name} ({idx + 1}/{total})...")
                            
                            # Apply lens corrections first if enabled
                            if apply_lens_correction:
                                corrected_path = str(Path(temp_dir) / f"corrected_{idx}_{file.name}")
                                lens_result = apply_lens_corrections(
                                    str(input_path),
                                    corrected_path,
                                    selected_lens=batch_lens if batch_lens != "None (Auto-detect from EXIF)" else None,
                                    focal_length=float(batch_focal.replace('mm', '')) if batch_focal else None
                                )
                            else:
                                # Skip lens corrections
                                lens_result = {'corrections_applied': False}
                                corrected_path = str(input_path)
                            
                            # Use corrected image if corrections were applied
                            if lens_result.get('corrections_applied'):
                                process_path = corrected_path
                                # Add lens info to status for batch mode
                                if lens_result.get('detected_from_exif'):
                                    status_text.text(f"Processing {file.name} ({idx + 1}/{total}) - Lens: {lens_result.get('lens_used')}")
                            else:
                                process_path = str(input_path)
                            
                            # Add processing preferences to instructions
                            if batch_use_chunked_gemini:
                                os.environ["USE_CHUNKED_GEMINI"] = "true"
                                os.environ["USE_4K_MODE"] = "true" if batch_use_4k_mode else "false"
                                final_batch_instructions = f"[CHUNKED_GEMINI_MODE] {batch_instructions}"
                            elif batch_use_gemini:
                                final_batch_instructions = f"Apply Gemini AI enhancement: {batch_instructions}"
                            else:
                                final_batch_instructions = batch_instructions
                                if not batch_use_gemini:
                                    final_batch_instructions += " Skip Gemini."
                            
                            # Set targeted enhancement flag if enabled
                            if batch_use_targeted:
                                os.environ["USE_TARGETED_ENHANCEMENT"] = "true"
                            else:
                                os.environ["USE_TARGETED_ENHANCEMENT"] = "false"
                            
                            # Set Gemini skip flag
                            os.environ["SKIP_GEMINI"] = "true" if not batch_use_gemini and not batch_use_chunked_gemini else "false"
                            
                            # Set lens correction preference for batch
                            if not apply_lens_correction:
                                os.environ["SKIP_LENS_CORRECTION"] = "true"
                            else:
                                os.environ["SKIP_LENS_CORRECTION"] = "false"
                            
                            # Set ImageMagick preference for batch
                            if not batch_use_imagemagick:
                                os.environ["SKIP_IMAGEMAGICK"] = "true"
                            else:
                                os.environ["SKIP_IMAGEMAGICK"] = "false"
                            
                            # Set background removal preference
                            if not batch_remove_background:
                                os.environ["SKIP_BACKGROUND_REMOVAL"] = "true"
                            else:
                                os.environ["SKIP_BACKGROUND_REMOVAL"] = "false"

                                # Set background removal method for batch
                                if batch_bg_method != "Use sidebar settings":
                                    if batch_bg_method == "rembg (free)":
                                        os.environ["BACKGROUND_REMOVAL_METHOD"] = "rembg"
                                        os.environ["REMBG_MODEL"] = batch_rembg_model
                                        print(f"📦 Batch: Setting background removal to rembg with model {batch_rembg_model}")
                                    elif batch_bg_method == "remove.bg API":
                                        os.environ["BACKGROUND_REMOVAL_METHOD"] = "remove.bg"
                                        print(f"📦 Batch: Setting background removal to remove.bg")
                                    else:  # "auto"
                                        os.environ["BACKGROUND_REMOVAL_METHOD"] = "auto"
                                        print(f"📦 Batch: Setting background removal to auto")
                                else:
                                    print(f"📦 Batch: Using sidebar settings for background removal")
                                # Otherwise, sidebar settings are already set in os.environ

                            # Set auto-trim preference for batch
                            os.environ["IMAGEMAGICK_TRIM"] = "true" if batch_auto_trim else "false"

                            # Set defect repair flag
                            if batch_use_defect_repair:
                                os.environ["USE_DEFECT_REPAIR"] = "true"
                            else:
                                os.environ.pop("USE_DEFECT_REPAIR", None)
                            
                            # Build custom batch base config from sliders
                            if 'batch_base_gamma' in locals():
                                batch_base_parts = []
                                
                                # IMPORTANT: Order matters in ImageMagick!
                                
                                # 1. Gamma adjustment first
                                if batch_base_gamma != 1.0:
                                    batch_base_parts.append(f"-gamma {batch_base_gamma}")
                                
                                # 2. Brightness/Contrast
                                if batch_base_brightness != 0 or batch_base_contrast != 0:
                                    batch_base_parts.append(f"-brightness-contrast {batch_base_brightness}x{batch_base_contrast}")
                                
                                # 3. Highlight/Shadow adjustment
                                if batch_base_highlights != 0 or batch_base_shadows != 0:
                                    black_point = max(0, batch_base_shadows)
                                    white_point = min(100, 100 + batch_base_highlights)
                                    if black_point != 0 or white_point != 100:
                                        batch_base_parts.append(f"-level {black_point}%,{white_point}%")
                                
                                # 4. Saturation
                                if batch_base_saturation != 100:
                                    batch_base_parts.append(f"-modulate 100,{batch_base_saturation},100")
                                
                                # 5. Sharpening
                                batch_base_parts.append(f"-unsharp {batch_base_sharpness_radius}x{batch_base_sharpness_sigma}")
                                
                                # 6. Quality
                                batch_base_parts.append("-quality 95")
                                
                                # Set the batch base config for consistency
                                batch_config = " ".join(batch_base_parts)
                                os.environ["BATCH_IMAGEMAGICK_BASE"] = batch_config
                                print(f"🎛️ Set batch ImageMagick config: {batch_config}")
                            
                            # The workflow already handles Pregel invocation internally
                            result = await process_single_image_enhanced(
                                image_path=process_path,
                                custom_instructions=final_batch_instructions,
                                output_dir=temp_dir,
                                api_keys=api_keys
                            )
                            
                            if result.get("final_image"):
                                return {
                                    "success": True,
                                    "original_name": file.name,
                                    "output_path": result.get("final_image"),
                                    "quality": result.get('final_quality', result.get('quality_score', 'N/A')),
                                    "lens_detected": lens_result.get('lens_used') if lens_result.get('detected_from_exif') else None,
                                    "lens_corrected": lens_result.get('corrections_applied', False)
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
                        # If batch consistency is enabled, use the new workflow
                        if use_batch_consistency and len(uploaded_files) > 1:
                            from src.batch_consistency import process_batch_with_consistency
                            
                            # Save all files to temp directory first
                            image_paths = []
                            for idx, file in enumerate(uploaded_files):
                                # Handle AVIF conversion if needed
                                if Path(file.name).suffix.lower() == '.avif':
                                    # Convert AVIF to WebP
                                    from PIL import Image as PILImage
                                    import io
                                    
                                    img = PILImage.open(file)
                                    webp_buffer = io.BytesIO()
                                    img.save(webp_buffer, 'WEBP', quality=95, method=6)
                                    webp_buffer.seek(0)
                                    
                                    # Save as WebP
                                    input_path = Path(temp_dir) / f"input_{idx}_{Path(file.name).stem}.webp"
                                    with open(input_path, "wb") as f:
                                        f.write(webp_buffer.getvalue())
                                else:
                                    input_path = Path(temp_dir) / f"input_{idx}_{file.name}"
                                    with open(input_path, "wb") as f:
                                        f.write(file.getbuffer())
                                image_paths.append(str(input_path))
                            
                            # Apply lens corrections if needed
                            corrected_paths = []
                            for idx, path in enumerate(image_paths):
                                if apply_lens_correction:
                                    corrected_path = str(Path(temp_dir) / f"corrected_{idx}_{Path(path).name}")
                                    lens_result = apply_lens_corrections(
                                        path,
                                        corrected_path,
                                        selected_lens=batch_lens if batch_lens != "None (Auto-detect from EXIF)" else None,
                                        focal_length=float(batch_focal.replace('mm', '')) if batch_focal else None
                                    )
                                    if lens_result.get('corrections_applied'):
                                        corrected_paths.append(corrected_path)
                                    else:
                                        corrected_paths.append(path)
                                else:
                                    corrected_paths.append(path)
                            
                            # Set environment variables for processing options
                            os.environ["USE_TARGETED_ENHANCEMENT"] = "true" if batch_use_targeted else "false"
                            os.environ["SKIP_LENS_CORRECTION"] = "true"  # Already applied above
                            os.environ["SKIP_GEMINI"] = "true" if not batch_use_gemini and not batch_use_chunked_gemini else "false"
                            if batch_use_repair:
                                os.environ["SKIP_REPAIR"] = "false"
                                os.environ["DEFECT_SENSITIVITY"] = str(batch_defect_sensitivity)
                            else:
                                os.environ["SKIP_REPAIR"] = "true"
                            os.environ["SKIP_BACKGROUND_REMOVAL"] = "false" if batch_remove_background else "true"

                            # Set auto-trim preference for batch consistency mode
                            os.environ["IMAGEMAGICK_TRIM"] = "true" if batch_auto_trim else "false"

                            # Set background removal method for batch consistency mode
                            if batch_remove_background and batch_bg_method != "Use sidebar settings":
                                if batch_bg_method == "rembg (free)":
                                    os.environ["BACKGROUND_REMOVAL_METHOD"] = "rembg"
                                    os.environ["REMBG_MODEL"] = batch_rembg_model
                                elif batch_bg_method == "remove.bg API":
                                    os.environ["BACKGROUND_REMOVAL_METHOD"] = "remove.bg"
                                else:  # "auto"
                                    os.environ["BACKGROUND_REMOVAL_METHOD"] = "auto"

                            if batch_use_chunked_gemini:
                                os.environ["USE_CHUNKED_GEMINI"] = "true"
                                os.environ["USE_4K_MODE"] = "true" if batch_use_4k_mode else "false"
                                final_batch_instructions = f"[CHUNKED_GEMINI_MODE] {batch_instructions}"
                            elif batch_use_gemini:
                                final_batch_instructions = f"Apply Gemini AI enhancement: {batch_instructions}"
                            else:
                                final_batch_instructions = batch_instructions
                                if not batch_use_gemini:
                                    final_batch_instructions += " Skip Gemini."
                            
                            if not batch_use_imagemagick:
                                os.environ["SKIP_IMAGEMAGICK"] = "true"
                            else:
                                os.environ["SKIP_IMAGEMAGICK"] = "false"
                            
                            # Process with batch consistency
                            status_text.text("🔍 Analyzing batch for consistency...")
                            batch_result = await process_batch_with_consistency(
                                corrected_paths,
                                final_batch_instructions,
                                temp_dir,
                                max_concurrent
                            )
                            
                            # Convert results to expected format
                            all_results = []
                            for idx, result in enumerate(batch_result.get('results', [])):
                                if isinstance(result, dict) and result.get('final_image'):
                                    all_results.append({
                                        "success": True,
                                        "original_name": uploaded_files[idx].name,
                                        "output_path": result.get("final_image"),
                                        "quality": result.get('final_quality', result.get('quality_score', 'N/A')),
                                        "batch_consistent": True
                                    })
                                else:
                                    all_results.append({
                                        "success": False,
                                        "original_name": uploaded_files[idx].name if idx < len(uploaded_files) else f"image_{idx}",
                                        "error": str(result) if not isinstance(result, dict) else result.get('error', 'Unknown error')
                                    })
                            
                            return all_results
                        else:
                            # Original non-consistency batch processing
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
                    
                    # Show batch consistency info if it was used
                    if use_batch_consistency and len(uploaded_files) > 1 and 'batch_result' in locals():
                        batch_profile = batch_result.get('batch_profile')
                        if batch_profile:
                            st.info(f"""
                            🎯 **Batch Consistency Applied:**
                            - Enhancement Level: {batch_profile.get('enhancement_level', 'N/A')}
                            - Brightness Adjustment: {batch_profile.get('brightness_adjustment', 'N/A')}
                            - Lighting Style: {batch_profile.get('lighting_style', 'N/A')}
                            """)
                    
                    # Main metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Processed", len(results))
                    with col2:
                        st.metric("Successful", len(successful), delta=f"{len(successful)/len(results)*100:.0f}%")
                    with col3:
                        st.metric("Failed", len(failed))
                    
                    # Lens detection summary if auto-detect was used
                    if batch_lens == "None (Auto-detect from EXIF)" and successful:
                        detected_lenses = {}
                        corrected_count = 0
                        for result in successful:
                            if result.get('lens_detected'):
                                detected_lenses[result['lens_detected']] = detected_lenses.get(result['lens_detected'], 0) + 1
                            if result.get('lens_corrected'):
                                corrected_count += 1
                        
                        if detected_lenses:
                            st.subheader("📷 Lens Detection Summary")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.info(f"🔍 Auto-detected from EXIF: {sum(detected_lenses.values())} images")
                                for lens, count in detected_lenses.items():
                                    st.write(f"• **{lens}**: {count} image{'s' if count > 1 else ''}")
                            with col2:
                                st.success(f"✅ Lens corrections applied: {corrected_count} images")
                                if corrected_count < sum(detected_lenses.values()):
                                    st.warning(f"⚠️ {sum(detected_lenses.values()) - corrected_count} detected but not corrected")
                    
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
                                            st.image(enhanced_img, caption=f"{result['original_name'][:20]}", width="stretch")
                                            
                                            quality = result.get('quality', 'N/A')
                                            if quality != 'N/A':
                                                st.caption(f"Quality: {quality}/10")
                    
                    if failed:
                        st.subheader("❌ Failed to Process")
                        for result in failed:
                            st.error(f"**{result['original_name']}**: {result['error']}")

# Help & Guide Mode
elif mode == "❓ Help & Guide":
    st.header("📚 Complete User Guide")
    
    # Quick navigation
    st.markdown("""
    **Quick Links:** [Getting Started](#getting-started) | [Processing Options](#processing-options) | 
    [Tips & Tricks](#tips-tricks) | [Troubleshooting](#troubleshooting)
    """)
    
    # Getting Started
    st.subheader("🚀 Getting Started", anchor="getting-started")
    
    with st.expander("**Step 1: Set Up Your API Keys** (First time only)", expanded=True):
        st.markdown("""
        1. Look at the **left sidebar** under Settings
        2. Enter your API keys:
           - **Anthropic API Key** (Required) - Powers image analysis
           - **Gemini API Key** (Required for AI) - Powers AI editing
           - **Remove.bg API Key** (Optional) - For professional background removal
             • Can use free rembg ML models instead - no API key needed!
        3. Click **💾 Save Keys**
        
        ✅ Your keys are saved in your browser and will persist across sessions!
        """)
    
    with st.expander("**Step 2: Choose Your Mode**"):
        st.markdown("""
        - **🖼️ Single Image**: Perfect for testing settings or individual products
        - **📦 Batch Processing**: Process multiple images with consistent settings
        - **❓ Help & Guide**: You're here now!
        """)
    
    with st.expander("**Step 3: Process Your First Image**"):
        st.markdown("""
        1. Switch to **Single Image** mode
        2. Upload a product photo
        3. Leave default settings (they're optimized for most cases)
        4. Click **🚀 Process Image**
        5. Download your enhanced image!
        """)
    
    # Processing Options
    st.subheader("⚙️ Processing Options Explained", anchor="processing-options")
    
    with st.expander("**ImageMagick Optimization** (Default: ON)"):
        st.markdown("""
        **What it does:** Traditional image processing - sharpening, color correction, exposure adjustment
        
        **When to use:**
        - ✅ Always recommended as base enhancement
        - ✅ Fast and reliable
        - ✅ Gives consistent results
        
        **Turn OFF only if:** You want pure AI enhancement without any traditional processing
        
        **🆕 Custom Base Configuration:**
        - Adjust starting values with sliders in the sidebar
        - Live preview shows real-time effect on your image
        - Based on professional Darktable settings
        - AI adjustments are applied on top of your base settings
        """)
    
    with st.expander("**Gemini AI Enhancement** (Default: OFF)"):
        st.markdown("""
        **What it does:** AI-powered editing that understands natural language instructions
        
        **Pros:**
        - Can understand complex requests ("make chrome more reflective")
        - Handles difficult edits ImageMagick can't do
        
        **Cons:**
        - Slower processing
        - Lower resolution output (1024x1024)
        - Uses API quota
        
        **Best for:** Complex edits requiring AI understanding
        """)
    
    with st.expander("**Chunked Gemini (High-Res AI)** 🆕"):
        st.markdown("""
        **What it does:** Processes large images in chunks to maintain full resolution while using AI
        
        **When to use:**
        - Need AI editing AND high resolution
        - Have time for slower processing
        - Want best of both worlds
        
        **Note:** Much slower than other options
        """)
    
    with st.expander("**Targeted Enhancement** 🎯"):
        st.markdown("""
        **What it does:** Identifies specific areas (chrome, glass, textures) and enhances them individually
        
        **Only available when:**
        - ImageMagick is ON
        - Regular Gemini is OFF
        
        **Best for:** Products with mixed materials needing selective enhancement
        """)
    
    with st.expander("**Auto Defect Repair** 🔧"):
        st.markdown("""
        **What it does:** Automatically detects and repairs dust, scratches, and sensor defects
        
        **How it works:**
        1. **Detection:** Uses OpenCV to find dust spots, scratches, and hot pixels
        2. **Repair:** Applies G'MIC filters or OpenCV inpainting to fix defects
        3. **Smart Selection:** Chooses repair method based on defect type
        
        **Sensitivity Slider (0-100):**
        - **0-30:** Only obvious defects (recommended for textured products)
        - **40-60:** Balanced detection (default)
        - **70-100:** Aggressive detection (may affect intentional details)
        
        **Best for:** 
        - Product photos with dust or minor scratches
        - Sensor dust spots from camera
        - Small imperfections that shouldn't be there
        
        **Note:** 
        - Can be slow on large images
        - May remove intentional texture on very sensitive settings
        - When disabled, dust detection is removed from AI analysis prompt
        """)
    
    with st.expander("**Background Removal** (Default: ON)"):
        st.markdown("""
        **What it does:** Professionally removes backgrounds using Remove.bg API
        
        **Turn OFF for:**
        - Lifestyle shots where you want the background
        - Images already with transparent backgrounds
        - Saving API quota
        """)
    
    with st.expander("**🖼️ Background Removal Options** 🆕"):
        st.markdown("""
        **Three Methods Available:**

        **1. Auto Mode (Default)**
        - Intelligently chooses the best method
        - Uses remove.bg API if key provided
        - Falls back to free rembg if no API key

        **2. remove.bg API**
        - Professional quality results
        - Handles complex edges perfectly
        - Requires API key (get free credits at remove.bg)

        **3. rembg (Free ML Models)**
        - No API key needed - runs locally!
        - 17+ models available for different use cases:

        **Product Photography (Recommended):**
          • **bria-rmbg**: Best overall for products
          • **birefnet-general**: High quality, latest tech
          • **isnet-general-use**: High accuracy

        **General Purpose:**
          • **u2net**: Default, good balance
          • **u2netp**: Fast & lightweight (4MB)
          • **silueta**: Smaller size (43MB)

        **People & Portraits:**
          • **u2net_human_seg**: Hair & clothing
          • **birefnet-portrait**: Portrait optimized
          • **u2net_cloth_seg**: Clothing separation

        **Specialized:**
          • **isnet-anime**: Anime characters
          • **sam**: Interactive segmentation
          • **birefnet-massive**: Massive dataset trained

        - First run downloads model (4MB-1GB depending on model)
        - **Alpha Matting**: Enable for smoother edges

        **Pro Tips:**
        - Start with auto mode for convenience
        - Use rembg for unlimited free processing
        - bria-rmbg model works great for product photos
        """)

    with st.expander("**Lens Corrections** (Default: OFF)"):
        st.markdown("""
        **What it does:** Fixes optical distortions from your camera lens

        **Supported lenses:**
        - Sony FE 24-70mm F2.8 GM
        - Sony FE 90mm F2.8 Macro G OSS
        - Sony FE 50mm F1.4 GM
        - Sony FE 70-200mm F2.8 GM OSS

        **Turn ON if you see:**
        - Barrel distortion (curved edges)
        - Dark corners (vignetting)
        - Color fringing
        """)
    
    with st.expander("**🎛️ ImageMagick Base Configuration** 🆕"):
        st.markdown("""
        **What it does:** Lets you customize the starting point for image processing
        
        **Available Sliders:**
        - **Gamma (0.8-1.2):** Adjusts midtone brightness
        - **Brightness (-10 to +10):** Overall lightness
        - **Contrast (-10 to +10):** Difference between light and dark
        - **Saturation (90-120):** Color intensity
        - **Highlights (-10 to 0):** Brightest areas control
        - **Shadows (0 to +10):** Darkest areas control
        - **Sharpness Radius & Sigma:** Edge enhancement
        
        **Live Preview Feature:**
        - See changes in real-time as you adjust sliders
        - Preview appears when image is uploaded
        - Fast approximation for instant feedback
        - Final result will be even better quality
        
        **Pro Tips:**
        - Start with Darktable defaults (already set)
        - Make small adjustments and preview
        - AI will still optimize on top of your settings
        - Click "Reset to Darktable Defaults" to start over
        """)
    
    with st.expander("**🚀 AI Upscaling** (Experimental)"):
        st.markdown("""
        **What it does:** Upscales lower resolution Gemini outputs back to original size
        
        **Methods Available:**
        - **Enhanced Lanczos (Default):** Fast, high-quality local upscaling with sharpening
        - **Google AI Upscaling:** Cloud-based AI upscaling (experimental, variable quality)
        
        **When it's used:**
        - Automatically after Gemini AI editing (outputs at 1024x1024)
        - Restores images to original resolution
        - Applies smart sharpening to compensate for upscaling
        
        **Note:** Enhanced Lanczos provides excellent results for most product photos
        """)
    
    # Tips & Tricks
    st.subheader("💡 Tips & Tricks", anchor="tips-tricks")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### For Chrome/Metal Products")
        st.code("""
Instructions: "Enhance chrome reflections, 
increase contrast, make metals look 
premium and polished"

Settings: 
- ImageMagick: ON
- Targeted Enhancement: OFF (not yet optimized)
        """, language="text")
    
    with col2:
        st.markdown("### For Matte/Textured Products")
        st.code("""
Instructions: "Enhance texture details, 
improve lighting, maintain natural 
material appearance"

Settings:
- ImageMagick: ON
- Gemini: OFF
        """, language="text")
    
    st.markdown("### Batch Processing Best Practices")
    
    with st.expander("**Ensure Consistency Across Batches**"):
        st.markdown("""
        1. **Always enable Batch Consistency Mode** - This analyzes all images first
        2. **Group similar products** - Process chrome separately from wood
        3. **Test on single image first** - Find optimal settings before batch
        4. **Monitor early results** - Check first few to avoid wasting time
        5. **Use 3 concurrent workers** - Good balance of speed and stability
        """)
    
    with st.expander("**Using Auto Defect Repair in Batches**"):
        st.markdown("""
        **⚠️ Important:** Defect repair can significantly slow batch processing
        
        **Recommendations:**
        - **For dusty product photos:** Enable with sensitivity 40-50
        - **For clean studio shots:** Usually not needed
        - **Mixed batch:** Process dusty items separately
        - **Test first:** Check one image to dial in sensitivity
        
        **Pro tip:** If many images need repair, consider running them through a dedicated defect repair pass first
        """)
    
    # Quality Scores
    st.subheader("📊 Understanding Quality Scores")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Excellent", "9-10", delta="Ready to use", delta_color="normal")
    with col2:
        st.metric("Good", "7-8", delta="Minor issues", delta_color="normal")
    with col3:
        st.metric("Fair", "5-6", delta="May need touchup", delta_color="normal")
    with col4:
        st.metric("Poor", "<5", delta="Auto-retry", delta_color="inverse")
    
    st.info("Files scoring ≤8 get renamed with quality suffix (e.g., image-q7.webp)")
    
    # Troubleshooting
    st.subheader("🔧 Troubleshooting", anchor="troubleshooting")
    
    with st.expander("**Image too dark or too bright**"):
        st.markdown("""
        **Solution:**
        - Add to instructions: "Brighten slightly" or "Reduce exposure"
        - ImageMagick usually handles this automatically
        - Check if your original photo is properly exposed
        """)
    
    with st.expander("**Colors look wrong**"):
        st.markdown("""
        **Solution:**
        - Add to instructions: "Correct white balance, enhance natural colors"
        - Enable lens corrections if using wide-angle lens
        - Make sure your monitor is color-calibrated
        """)
    
    with st.expander("**Processing is too slow**"):
        st.markdown("""
        **Solution:**
        - Turn OFF Gemini/Chunked Gemini
        - Use ImageMagick only for speed
        - Reduce concurrent workers in batch mode
        - Process smaller batches
        """)
    
    with st.expander("**API Key errors**"):
        st.markdown("""
        **Solution:**
        - Check for extra spaces in your keys
        - Make sure keys are valid and have quota
        - Try saving keys again
        - Refresh the page after saving
        """)
    
    with st.expander("**Quality check keeps failing**"):
        st.markdown("""
        **Solution:**
        - System auto-retries up to 2 times
        - Try different instructions
        - Use more conservative settings
        - May need manual editing for difficult images
        """)
    
    # Workflow Overview
    st.subheader("🔄 How It Works")
    
    st.markdown("""
    ### The AI Pipeline Process:
    
    1. **📊 Analysis** - Claude examines your image and identifies issues
    2. **🔧 Defect Detection** - Finds dust/scratches (if enabled)
    3. **🩹 Defect Repair** - G'MIC/OpenCV repairs defects (if enabled)
    4. **📷 Lens Correction** - Fixes optical distortions (if enabled)
    5. **✨ Enhancement** - ImageMagick (with your base config) and/or Gemini improve the image
    6. **🖼️ Background Removal** - Creates transparent background (if enabled)
    7. **🎯 Targeted Enhancement** - Surgical improvements to specific areas (if enabled)
    8. **📐 Upscaling** - Restores resolution after AI editing (automatic)
    9. **✅ Quality Control** - Claude checks the result and may retry if needed
    
    Each step is optimized for product photography!
    """)
    
    # Contact and Resources
    st.subheader("📞 Need More Help?")
    
    st.markdown("""
    - **Error messages are descriptive** - Read them carefully
    - **Check the console** for detailed logs (F12 in browser)
    - **Most issues are API related** - Check your quotas
    - **GitHub Issues**: Report bugs or request features
    
    ---
    
    💡 **Pro Tip**: Start with conservative settings and increase enhancement gradually. 
    Less is often more in product photography!
    
    ### Recent Updates 🆕
    - **Real-time preview** for ImageMagick adjustments
    - **Custom base configuration** with Darktable-inspired defaults
    - **Enhanced Lanczos upscaling** for better Gemini output quality
    - **Smarter dust detection** - only when defect repair is enabled
    - **Unified Wand agent** for more reliable ImageMagick processing
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    Made with ❤️ for Doug using LangGraph, Claude Sonnet 4, and Gemini 2.5 Flash<br>
    <a href='https://github.com/pranavchavda/langgraph-photo-editor'>GitHub</a> | 
    Your API keys never leave your browser
</div>
""", unsafe_allow_html=True)