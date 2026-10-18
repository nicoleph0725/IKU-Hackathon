"""Vercel entry point: serves the Flask app in backend/ as a serverless function.

vercel.json sends every /api/* request here; Flask still sees the original path.
"""
import os
import sys

# backend/ uses flat imports (import auth, from db import ...), so put it on the path.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

from app import app  # noqa: E402,F401
