"""
Doug's Photo Editor - Simple Version with Working Key Persistence
"""

import streamlit as st
import asyncio
from pathlib import Path
import tempfile
from PIL import Image
import os
import streamlit.components.v1 as components

# Import our existing workflow
from src.workflow_enhanced import process_single_image_enhanced

# Try to use advanced lens corrections
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

# Initialize session state that actually persists
for key in ['processed_image', 'processed_image_data', 'processed_filename', 'processing_metrics']:
    if key not in st.session_state:
        st.session_state[key] = None

# CRITICAL: Use st.session_state for API keys with widget callbacks
if 'keys' not in st.session_state:
    st.session_state.keys = {'anthropic': '', 'gemini': '', 'removebg': ''}

# JavaScript to sync with localStorage after page fully loads
js_sync = """
<script>
// Wait for page to fully load
window.addEventListener('load', () => {
    setTimeout(() => {
        // Load from localStorage
        const keys = {
            anthropic: localStorage.getItem('doug_anthropic') || '',
            gemini: localStorage.getItem('doug_gemini') || '',
            removebg: localStorage.getItem('doug_removebg') || ''
        };
        
        console.log('Keys in localStorage:', {
            anthropic: !!keys.anthropic,
            gemini: !!keys.gemini,
            removebg: !!keys.removebg
        });
        
        // Find password inputs and populate
        const inputs = document.querySelectorAll('input[type="password"]');
        if (inputs.length >= 3) {
            if (keys.anthropic && !inputs[0].value) {
                inputs[0].value = keys.anthropic;
                inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
            }
            if (keys.gemini && !inputs[1].value) {
                inputs[1].value = keys.gemini;
                inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
            }
            if (keys.removebg && !inputs[2].value) {
                inputs[2].value = keys.removebg;
                inputs[2].dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
        
        // Save on change
        inputs.forEach((input, idx) => {
            input.addEventListener('change', () => {
                const keyNames = ['doug_anthropic', 'doug_gemini', 'doug_removebg'];
                if (input.value) {
                    localStorage.setItem(keyNames[idx], input.value);
                    console.log(`Saved ${keyNames[idx]}`);
                }
            });
        });
    }, 500);
});
</script>
"""

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("API Keys")
    st.caption("Keys are saved in your browser")
    
    # Use callbacks to update session state
    def save_key(key_name):
        def callback():
            val = st.session_state[f"{key_name}_widget"]
            st.session_state.keys[key_name] = val
            # Also trigger JavaScript save
            js = f"""
            <script>
            localStorage.setItem('doug_{key_name}', '{val}');
            console.log('Saved {key_name} to localStorage');
            </script>
            """
            components.html(js, height=0)
        return callback
    
    anthropic_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=st.session_state.keys['anthropic'],
        key="anthropic_widget",
        on_change=save_key('anthropic')
    )
    
    gemini_key = st.text_input(
        "Gemini API Key",
        type="password",
        value=st.session_state.keys['gemini'],
        key="gemini_widget",
        on_change=save_key('gemini')
    )
    
    removebg_key = st.text_input(
        "Remove.bg API Key (Optional)",
        type="password",
        value=st.session_state.keys['removebg'],
        key="removebg_widget",
        on_change=save_key('removebg')
    )
    
    # Update session state with current values
    st.session_state.keys['anthropic'] = anthropic_key
    st.session_state.keys['gemini'] = gemini_key
    st.session_state.keys['removebg'] = removebg_key
    
    st.subheader("Options")
    use_gemini = st.checkbox("Use Gemini 2.5 Flash", value=True)
    
    st.subheader("📷 Lens Corrections")
    lens_options = get_lens_options()
    selected_lens = st.selectbox(
        "Select lens:",
        lens_options,
        index=len(lens_options) - 1
    )

# Inject JS sync
components.html(js_sync, height=0)

# Main content
st.title("📸 Doug's Photo Editor")

col1, col2 = st.columns(2)

with col1:
    st.header("Upload")
    uploaded_file = st.file_uploader("Choose an image...", type=['png', 'jpg', 'jpeg', 'webp'])
    
    if uploaded_file:
        st.image(uploaded_file, caption="Original")
        
    instructions = st.text_area("Instructions (optional)", placeholder="e.g. enhance chrome")
    process_btn = st.button("🚀 Process Image", type="primary")

with col2:
    st.header("Result")
    
    if st.session_state.processed_image:
        st.image(st.session_state.processed_image, caption="Enhanced")
        st.download_button(
            "⬇️ Download",
            st.session_state.processed_image_data,
            st.session_state.processed_filename,
            mime="image/webp"
        )
    else:
        st.info("Upload and process an image")

# Process image
if uploaded_file and process_btn:
    # Use keys from session state
    anthropic = st.session_state.keys['anthropic']
    gemini = st.session_state.keys['gemini']
    removebg = st.session_state.keys['removebg']
    
    if not anthropic:
        st.error("Enter Anthropic API key")
    elif use_gemini and not gemini:
        st.error("Enter Gemini API key")
    else:
        os.environ["ANTHROPIC_API_KEY"] = anthropic
        os.environ["GEMINI_API_KEY"] = gemini
        if removebg:
            os.environ["REMOVE_BG_API_KEY"] = removebg
        
        with st.spinner("Processing..."):
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Save input
                    input_path = Path(temp_dir) / uploaded_file.name
                    input_path.write_bytes(uploaded_file.getbuffer())
                    
                    # Lens corrections
                    corrected_path = Path(temp_dir) / f"corrected_{uploaded_file.name}"
                    lens_result = apply_lens_corrections(
                        str(input_path),
                        str(corrected_path),
                        selected_lens=selected_lens if selected_lens != "None (Auto-detect from EXIF)" else None
                    )
                    
                    if lens_result.get('corrections_applied'):
                        st.info(f"📷 {lens_result.get('message', '')}")
                        process_path = str(corrected_path)
                    else:
                        process_path = str(input_path)
                    
                    # Process
                    result = asyncio.run(process_single_image_enhanced(
                        image_path=process_path,
                        custom_instructions=instructions,
                        output_dir=temp_dir
                    ))
                    
                    if result.get("final_image"):
                        output = Path(result["final_image"])
                        if output.exists():
                            st.session_state.processed_image = Image.open(output)
                            st.session_state.processed_image_data = output.read_bytes()
                            st.session_state.processed_filename = f"enhanced_{uploaded_file.name}"
                            st.success("✅ Done!")
                            st.rerun()
                    else:
                        st.error(f"Failed: {result.get('error', 'Unknown error')}")
                        
            except Exception as e:
                st.error(f"Error: {str(e)}")