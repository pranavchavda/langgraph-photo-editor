"""
Local storage helper for Streamlit to persist API keys in browser
"""

import streamlit as st
import streamlit.components.v1 as components
import json

def init_local_storage():
    """Initialize localStorage handler and retrieve stored values"""
    
    # JavaScript to handle localStorage
    local_storage_script = """
    <script>
    // Function to save to localStorage
    function saveToLocalStorage(key, value) {
        localStorage.setItem('photoEditor_' + key, value);
    }
    
    // Function to get from localStorage
    function getFromLocalStorage(key) {
        return localStorage.getItem('photoEditor_' + key);
    }
    
    // Function to send stored values back to Streamlit
    function sendStoredValues() {
        const stored = {
            anthropic: getFromLocalStorage('anthropic') || '',
            gemini: getFromLocalStorage('gemini') || '',
            removebg: getFromLocalStorage('removebg') || ''
        };
        
        // Send to parent using postMessage
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            data: stored
        }, '*');
    }
    
    // Load stored values on page load
    document.addEventListener('DOMContentLoaded', function() {
        // Retrieve and populate stored values
        const anthropicStored = getFromLocalStorage('anthropic');
        const geminiStored = getFromLocalStorage('gemini');
        const removebgStored = getFromLocalStorage('removebg');
        
        // Try to find and populate the input fields
        setTimeout(() => {
            const inputs = document.querySelectorAll('input[type="password"]');
            if (inputs.length >= 1 && anthropicStored) {
                inputs[0].value = anthropicStored;
                inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
            }
            if (inputs.length >= 2 && geminiStored) {
                inputs[1].value = geminiStored;
                inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
            }
            if (inputs.length >= 3 && removebgStored) {
                inputs[2].value = removebgStored;
                inputs[2].dispatchEvent(new Event('input', { bubbles: true }));
            }
        }, 500);
    });
    
    // Save when inputs change
    setInterval(() => {
        const inputs = document.querySelectorAll('input[type="password"]');
        if (inputs.length >= 1 && inputs[0].value) {
            saveToLocalStorage('anthropic', inputs[0].value);
        }
        if (inputs.length >= 2 && inputs[1].value) {
            saveToLocalStorage('gemini', inputs[1].value);
        }
        if (inputs.length >= 3 && inputs[2].value) {
            saveToLocalStorage('removebg', inputs[2].value);
        }
    }, 1000);
    </script>
    """
    
    components.html(local_storage_script, height=0)

def get_stored_keys():
    """
    Retrieve stored API keys from localStorage
    Returns dict with keys: anthropic, gemini, removebg
    """
    # This is a placeholder - in practice, we'll use the session state
    # that gets populated by the JavaScript
    return st.session_state.get('stored_keys', {
        'anthropic': '',
        'gemini': '',
        'removebg': ''
    })

def save_keys_to_storage(anthropic_key, gemini_key, removebg_key):
    """Save keys to localStorage via JavaScript injection"""
    
    save_script = f"""
    <script>
    localStorage.setItem('photoEditor_anthropic', '{anthropic_key}');
    localStorage.setItem('photoEditor_gemini', '{gemini_key}');
    localStorage.setItem('photoEditor_removebg', '{removebg_key}');
    </script>
    """
    
    components.html(save_script, height=0)