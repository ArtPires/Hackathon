"""FastAPI application entry point."""
import os
import logging
from fastapi import FastAPI
from app.api.routes import router

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

# Ensure output directories exist
for d in ["outputs/reports", "outputs/videos", "assets/videos"]:
    os.makedirs(d, exist_ok=True)

app = FastAPI(
    title="Traffic Inspection Agent",
    description="Embodied agent that uses reusable skills to inspect traffic feeds.",
    version="0.1.0",
)

app.include_router(router)
