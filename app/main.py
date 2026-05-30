"""FastAPI Application Entrypoint (Phase 4)."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.data.repository import RestaurantRepository
from config.settings import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Load repository data on startup."""
    logger.info("Initializing Restaurant Repository...")
    try:
        # Load from cache or download from Hugging Face
        repo = RestaurantRepository.from_cache_or_dataset()
        app.state.repository = repo
        logger.info("Restaurant Repository successfully loaded. Count: %d", repo.count)
    except Exception as exc:
        logger.critical("Failed to load restaurant dataset on startup: %s", exc, exc_info=True)
        # Keep app running but repository is None so endpoints will fail with 503
        app.state.repository = None

    yield
    
    logger.info("Shutting down Application...")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="Zomato AI Recommendation API",
        version="1.0.0",
        description="API serving deterministic and LLM-powered restaurant recommendations",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount the React dist folder to serve compiled UI files
    from fastapi.staticfiles import StaticFiles
    import os
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    dist_dir = os.path.join(project_root, "frontend", "dist")
    reimagining_dir = os.path.join(project_root, "stitch_zomato_ai_visual_reimagining")
    
    if os.path.exists(dist_dir):
        app.mount(
            "/ui",
            StaticFiles(directory=dist_dir, html=True),
            name="ui"
        )
    elif os.path.exists(reimagining_dir):
        app.mount(
            "/ui",
            StaticFiles(directory=reimagining_dir),
            name="ui"
        )


    # Include routes
    app.include_router(router)

    return app


app = create_app()
