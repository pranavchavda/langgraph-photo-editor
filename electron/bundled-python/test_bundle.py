#!/usr/bin/env python3
import sys
import os

print("Python Bundle Test")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Python path: {os.pathsep.join(sys.path)}")

# Test importing key dependencies
try:
    import anthropic
    print("✓ anthropic imported successfully")
except ImportError as e:
    print(f"✗ Failed to import anthropic: {e}")

try:
    import google.generativeai
    print("✓ google.generativeai imported successfully")
except ImportError as e:
    print(f"✗ Failed to import google.generativeai: {e}")

try:
    import langgraph
    print("✓ langgraph imported successfully")
except ImportError as e:
    print(f"✗ Failed to import langgraph: {e}")

print("Bundle test complete!")
