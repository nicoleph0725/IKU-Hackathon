"""Flask backend. Empty for now: we'll add API routes here as we build features."""
from flask import Flask

app = Flask(__name__)




@app.get("/api/health")
def health():
    """Quick check that the backend is running."""
    return {"status": "ok"}
