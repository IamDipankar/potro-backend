#!/usr/bin/env python3
"""
Entry point for the FastAPI application.
Run this script to start the server.
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ngl.main:app", host="0.0.0.0", port=8000, reload=True)
