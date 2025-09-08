"""
Browser Storage Component for Streamlit
Handles localStorage persistence for API keys
"""

import streamlit as st
import streamlit.components.v1 as components
import json
from typing import Dict, Optional

def get_storage_manager():
    """Returns a JavaScript component that manages localStorage"""
    
    js_code = """
    <div id="storage-manager"></div>
    <script>
    (function() {
        // Function to get stored keys
        function getStoredKeys() {
            return {
                anthropic: localStorage.getItem('doug_anthropic') || '',
                gemini: localStorage.getItem('doug_gemini') || '',
                removebg: localStorage.getItem('doug_removebg') || ''
            };
        }
        
        // Function to save keys
        window.saveApiKeys = function(anthropic, gemini, removebg) {
            if (anthropic) localStorage.setItem('doug_anthropic', anthropic);
            if (gemini) localStorage.setItem('doug_gemini', gemini);
            if (removebg) localStorage.setItem('doug_removebg', removebg);
            return true;
        };
        
        // Send stored keys to parent window
        const storedKeys = getStoredKeys();
        
        // Try to update Streamlit inputs if they exist and are empty
        const tryUpdateInputs = () => {
            const inputs = parent.document.querySelectorAll('input[type="password"]');
            if (inputs.length >= 3) {
                // Check if inputs are empty before setting
                if (!inputs[0].value && storedKeys.anthropic) {
                    // Use Streamlit's internal method to set value
                    const setNativeValue = (element, value) => {
                        const valueSetter = Object.getOwnPropertyDescriptor(element.__proto__, 'value').set;
                        const prototype = Object.getPrototypeOf(element);
                        const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value').set;
                        
                        if (valueSetter && valueSetter !== prototypeValueSetter) {
                            prototypeValueSetter.call(element, value);
                        } else {
                            valueSetter.call(element, value);
                        }
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                    };
                    
                    setNativeValue(inputs[0], storedKeys.anthropic);
                }
                if (!inputs[1].value && storedKeys.gemini) {
                    const setNativeValue = (element, value) => {
                        const valueSetter = Object.getOwnPropertyDescriptor(element.__proto__, 'value').set;
                        const prototype = Object.getPrototypeOf(element);
                        const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value').set;
                        
                        if (valueSetter && valueSetter !== prototypeValueSetter) {
                            prototypeValueSetter.call(element, value);
                        } else {
                            valueSetter.call(element, value);
                        }
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                    };
                    
                    setNativeValue(inputs[1], storedKeys.gemini);
                }
                if (!inputs[2].value && storedKeys.removebg) {
                    const setNativeValue = (element, value) => {
                        const valueSetter = Object.getOwnPropertyDescriptor(element.__proto__, 'value').set;
                        const prototype = Object.getPrototypeOf(element);
                        const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value').set;
                        
                        if (valueSetter && valueSetter !== prototypeValueSetter) {
                            prototypeValueSetter.call(element, value);
                        } else {
                            valueSetter.call(element, value);
                        }
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                    };
                    
                    setNativeValue(inputs[2], storedKeys.removebg);
                }
                
                // Set up save listeners
                inputs.forEach((input, idx) => {
                    input.addEventListener('change', () => {
                        const values = Array.from(inputs).map(i => i.value);
                        if (values[0]) localStorage.setItem('doug_anthropic', values[0]);
                        if (values[1]) localStorage.setItem('doug_gemini', values[1]);
                        if (values[2]) localStorage.setItem('doug_removebg', values[2]);
                    });
                });
                
                return true;
            }
            return false;
        };
        
        // Try multiple times to ensure inputs are ready
        let attempts = 0;
        const interval = setInterval(() => {
            if (tryUpdateInputs() || attempts > 10) {
                clearInterval(interval);
            }
            attempts++;
        }, 500);
        
    })();
    </script>
    """
    
    return js_code

def load_stored_keys() -> Dict[str, str]:
    """Load API keys from localStorage via JavaScript bridge"""
    
    # Check session state first
    if 'stored_keys' not in st.session_state:
        st.session_state.stored_keys = {
            'anthropic': '',
            'gemini': '',
            'removebg': ''
        }
    
    # Inject the storage manager
    components.html(get_storage_manager(), height=0)
    
    return st.session_state.stored_keys

def save_keys(anthropic: str, gemini: str, removebg: str):
    """Save API keys to localStorage"""
    
    js_save = f"""
    <script>
    localStorage.setItem('doug_anthropic', '{anthropic}');
    localStorage.setItem('doug_gemini', '{gemini}');
    localStorage.setItem('doug_removebg', '{removebg}');
    console.log('Keys saved to localStorage');
    </script>
    """
    
    components.html(js_save, height=0)
    
    # Also update session state
    st.session_state.stored_keys = {
        'anthropic': anthropic,
        'gemini': gemini,
        'removebg': removebg
    }