#!/usr/bin/env python
"""Test script to validate all imports"""
import sys
import traceback

print("Testing imports...")

# Test 1: Streamlit
try:
    import streamlit as st
    print("✓ streamlit")
except Exception as e:
    print(f"✗ streamlit: {e}")
    traceback.print_exc()

# Test 2: Database
try:
    from database import init_db, SessionLocal
    print("✓ database")
except Exception as e:
    print(f"✗ database: {e}")
    traceback.print_exc()

# Test 3: Utils
try:
    from utils import apply_theme, init_session_defaults
    print("✓ utils")
except Exception as e:
    print(f"✗ utils: {e}")
    traceback.print_exc()

# Test 4: CV Engine
try:
    from cv_engine import CVProcessor
    print("✓ cv_engine")
except Exception as e:
    print(f"✗ cv_engine: {e}")
    traceback.print_exc()

# Test 5: Gemini Utils
try:
    from gemini_utils import generate_coach_response
    print("✓ gemini_utils")
except Exception as e:
    print(f"✗ gemini_utils: {e}")
    traceback.print_exc()

print("\nAll tests completed!")
