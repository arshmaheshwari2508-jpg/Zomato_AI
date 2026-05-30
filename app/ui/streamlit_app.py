"""Streamlit User Interface for Zomato AI (Phase 5) - Luminous Gastronomy Design."""

from __future__ import annotations

import logging
import textwrap
import httpx
import streamlit as st

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


def check_api_status() -> bool:
    """Check if the FastAPI API server is online and has loaded the dataset."""
    try:
        response = httpx.get(f"{API_URL}/health", timeout=1.0)
        return response.status_code == 200 and response.json().get("dataset_loaded", False)
    except Exception:
        return False


def load_dataset_hints(use_api: bool) -> tuple[list[str], list[str], list[str], list[str]]:
    """Load hint options for cities, location_options, cuisines, and budget tiers."""
    if use_api:
        try:
            response = httpx.get(f"{API_URL}/dataset/stats", timeout=3.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("cities", []), data.get("location_options", []), data.get("cuisines", []), data.get("budget_tiers", [])
        except Exception as exc:
            logger.error("Failed to load dataset stats from API: %s", exc)
    
    # Fallback to direct repository loading
    try:
        from app.data.repository import RestaurantRepository
        from app.domain.filter import FilterService
        
        repo = RestaurantRepository.from_cache_or_dataset()
        filter_service = FilterService(repo)
        hints = filter_service.get_dataset_hints()
        return hints.cities, hints.location_options, hints.cuisines, hints.budget_tiers
    except Exception as exc:
        logger.error("Local fallback failed to load dataset hints: %s", exc)
        return ["Bangalore"], ["Bangalore"], ["Italian", "Chinese", "North Indian", "Continental"], ["low", "medium", "high"]


def get_recommendations(preferences: dict, use_api: bool) -> dict:
    """Fetch recommendations from API or execute in-process."""
    if use_api:
        try:
            response = httpx.post(f"{API_URL}/recommendations", json=preferences, timeout=65.0)
            if response.status_code == 200:
                return response.json()
            return {"success": False, "error": f"API server returned error {response.status_code}: {response.text}"}
        except Exception as exc:
            return {"success": False, "error": f"Failed to connect to API server: {exc}"}
            
    # Local in-process fallback
    try:
        from app.domain.models import UserPreferences, UserBudget
        from app.domain.orchestrator import RecommendationOrchestrator
        from app.data.repository import RestaurantRepository
        from app.domain.filter import FilterService
        
        repo = RestaurantRepository.from_cache_or_dataset()
        filter_service = FilterService(repo)
        orchestrator = RecommendationOrchestrator(filter_service=filter_service)
        
        prefs = UserPreferences(
            location=preferences["location"],
            budget=UserBudget(preferences["budget"]),
            cuisine=preferences["cuisine"],
            min_rating=preferences["min_rating"],
            additional_preferences=preferences["additional_preferences"],
            top_k=preferences["top_k"]
        )
        result = orchestrator.recommend(prefs)
        return result.model_dump()
    except Exception as exc:
        return {"success": False, "error": f"In-process engine execution failed: {exc}"}


# ----------------------------------------------------
# Page Layout & Luminous Gastronomy Design System
# ----------------------------------------------------
st.set_page_config(
    page_title="CraveAI - Restaurant Recommendations",
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Luminous Gastronomy Design System CSS
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');
    
    :root {
        /* Luminous Gastronomy Color Palette */
        --primary: #b7122a;
        --primary-container: #db313f;
        --on-primary: #ffffff;
        --on-primary-container: #fffbff;
        --primary-fixed: #ffdad8;
        --primary-fixed-dim: #ffb3b1;
        --on-primary-fixed: #410007;
        --on-primary-fixed-variant: #92001c;
        
        --secondary: #b90040;
        --secondary-container: #de2656;
        --on-secondary: #ffffff;
        --on-secondary-container: #fffbff;
        --secondary-fixed: #ffd9dc;
        --secondary-fixed-dim: #ffb2ba;
        --on-secondary-fixed: #400011;
        --on-secondary-fixed-variant: #910031;
        
        --tertiary: #b51c00;
        --tertiary-container: #dc3214;
        --on-tertiary: #ffffff;
        --on-tertiary-container: #fffbff;
        --tertiary-fixed: #ffdad3;
        --tertiary-fixed-dim: #ffb4a5;
        --on-tertiary-fixed: #3e0400;
        --on-tertiary-fixed-variant: #8e1300;
        
        --error: #ba1a1a;
        --error-container: #ffdad6;
        --on-error: #ffffff;
        --on-error-container: #93000a;
        
        --background: #fcf9f8;
        --on-background: #1b1b1b;
        --surface: #fcf9f8;
        --on-surface: #1b1b1b;
        --surface-variant: #e5e2e1;
        --on-surface-variant: #5b403f;
        --outline: #8f6f6e;
        --outline-variant: #e4bebc;
        
        --surface-container-lowest: #ffffff;
        --surface-container-low: #f6f3f2;
        --surface-container: #f0eded;
        --surface-container-high: #eae7e7;
        --surface-container-highest: #e5e2e1;
        --surface-dim: #dcd9d9;
        --surface-bright: #fcf9f8;
        
        --inverse-surface: #313030;
        --inverse-on-surface: #f3f0ef;
        --inverse-primary: #ffb3b1;
        --surface-tint: #bb162c;
    }
    
    /* Dark Mode Variables */
    .dark {
        --background: #1b1b1b;
        --on-background: #f3f0ef;
        --surface: #1b1b1b;
        --on-surface: #f3f0ef;
        --surface-variant: #3e3e3e;
        --on-surface-variant: #c4c4c4;
        --outline: #9e9090;
        --outline-variant: #4a4545;
        --surface-container-lowest: #1b1b1b;
        --surface-container-low: #2a2a2a;
        --surface-container: #2e2e2e;
        --surface-container-high: #383838;
        --surface-container-highest: #424242;
        --surface-dim: #f3f0ef;
        --surface-bright: #1b1b1b;
    }
    
    /* Global Styles */
    .stApp {
        background-color: var(--background);
        color: var(--on-background);
    }
    
    /* Typography */
    .font-display-lg {
        font-family: 'Outfit', sans-serif;
        font-size: 48px;
        font-weight: 700;
        line-height: 56px;
        letter-spacing: -0.02em;
    }
    
    .font-headline-lg {
        font-family: 'Outfit', sans-serif;
        font-size: 32px;
        font-weight: 600;
        line-height: 40px;
        letter-spacing: -0.01em;
    }
    
    .font-headline-md {
        font-family: 'Outfit', sans-serif;
        font-size: 24px;
        font-weight: 600;
        line-height: 32px;
    }
    
    .font-body-lg {
        font-family: 'Inter', sans-serif;
        font-size: 18px;
        font-weight: 400;
        line-height: 28px;
    }
    
    .font-body-md {
        font-family: 'Inter', sans-serif;
        font-size: 16px;
        font-weight: 400;
        line-height: 24px;
    }
    
    .font-body-sm {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 400;
        line-height: 20px;
    }
    
    .font-label-md {
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 600;
        line-height: 16px;
        letter-spacing: 0.05em;
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .dark .glass-card {
        background: rgba(27, 27, 27, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .glass-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 20px -5px rgba(0, 0, 0, 0.08);
    }
    
    /* Premium Restaurant Card */
    .restaurant-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    
    .dark .restaurant-card {
        background: rgba(27, 27, 27, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .restaurant-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 20px -5px rgba(0, 0, 0, 0.08);
    }
    
    .restaurant-image {
        width: 100%;
        height: 200px;
        object-fit: cover;
        transition: transform 0.7s ease;
    }
    
    .restaurant-card:hover .restaurant-image {
        transform: scale(1.1);
    }
    
    .rank-badge {
        position: absolute;
        top: 12px;
        right: 12px;
        background: linear-gradient(135deg, #b7122a, #db313f);
        color: white;
        font-weight: 700;
        font-size: 14px;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 10px rgba(183, 18, 42, 0.25);
        z-index: 10;
    }
    
    .rating-badge {
        position: absolute;
        top: 12px;
        left: 12px;
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 13px;
        display: flex;
        align-items: center;
        gap: 4px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        z-index: 10;
    }
    
    .rating-badge .star {
        color: #b7122a;
    }
    
    .premium-badge {
        position: absolute;
        top: 12px;
        left: 50%;
        transform: translateX(-50%);
        background: var(--primary);
        color: white;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 12px rgba(183, 18, 42, 0.3);
        z-index: 10;
    }
    
    .restaurant-name {
        font-family: 'Outfit', sans-serif;
        font-size: 20px;
        font-weight: 700;
        color: var(--on-surface);
        margin-bottom: 4px;
    }
    
    .restaurant-location {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        color: var(--on-surface-variant);
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    .cost-badge {
        font-family: 'Outfit', sans-serif;
        font-size: 18px;
        font-weight: 700;
        color: var(--primary);
    }
    
    .ai-explanation {
        background: rgba(183, 18, 42, 0.05);
        border: 1px solid rgba(183, 18, 42, 0.1);
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 13px;
        font-family: 'Inter', sans-serif;
        line-height: 1.5;
        color: var(--on-surface-variant);
    }
    
    .ai-explanation::before {
        content: '✨ AI Reason:';
        display: block;
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--primary);
        margin-bottom: 6px;
    }
    
    /* Stepper Styles */
    .stepper-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 40px;
        margin-bottom: 32px;
        position: relative;
    }
    
    .stepper-line {
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 2px;
        background: var(--outline-variant);
        transform: translateY(-50%);
        z-index: 0;
    }
    
    .stepper-progress {
        position: absolute;
        top: 50%;
        left: 0;
        height: 2px;
        background: var(--primary);
        transform: translateY(-50%);
        z-index: 0;
        transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .step-indicator {
        position: relative;
        z-index: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
    }
    
    .step-circle {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        transition: all 0.3s ease;
    }
    
    .step-circle.active {
        background: var(--primary);
        color: var(--on-primary);
        box-shadow: 0 0 0 4px rgba(183, 18, 42, 0.2);
    }
    
    .step-circle.completed {
        background: var(--primary);
        color: var(--on-primary);
    }
    
    .step-circle.inactive {
        background: var(--surface-container-high);
        color: var(--on-surface-variant);
    }
    
    .step-label {
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    
    .step-label.active {
        color: var(--primary);
    }
    
    .step-label.inactive {
        color: var(--on-surface-variant);
    }
    
    /* Cuisine Chips */
    .cuisine-chip {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 16px;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .cuisine-chip:hover {
        border-color: var(--primary);
        background: rgba(183, 18, 42, 0.05);
    }
    
    .cuisine-chip.selected {
        border: 2px solid var(--primary);
        background: rgba(183, 18, 42, 0.05);
    }
    
    .cuisine-icon {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 12px;
        background: var(--surface-container);
        transition: all 0.3s ease;
    }
    
    .cuisine-chip.selected .cuisine-icon {
        background: var(--primary);
    }
    
    .cuisine-chip.selected .cuisine-icon span {
        color: var(--on-primary);
    }
    
    /* Budget Slider */
    .budget-container {
        padding: 24px;
    }
    
    .budget-label {
        font-family: 'Outfit', sans-serif;
        font-size: 24px;
        font-weight: 600;
        color: var(--on-surface);
        margin-bottom: 8px;
    }
    
    .budget-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 16px;
        color: var(--on-surface-variant);
        margin-bottom: 32px;
    }
    
    /* Preset Cards */
    .preset-card {
        position: relative;
        height: 128px;
        border-radius: 16px;
        overflow: hidden;
        cursor: pointer;
        transition: transform 0.3s ease;
    }
    
    .preset-card:hover {
        transform: scale(1.05);
    }
    
    .preset-card img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.5s ease;
    }
    
    .preset-card:hover img {
        transform: scale(1.1);
    }
    
    .preset-overlay {
        position: absolute;
        inset: 0;
        background: rgba(0, 0, 0, 0.4);
        display: flex;
        align-items: flex-end;
        padding: 12px;
    }
    
    .preset-card.selected .preset-overlay {
        background: rgba(183, 18, 42, 0.2);
    }
    
    .preset-label {
        color: white;
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    
    .preset-check {
        position: absolute;
        top: 8px;
        right: 8px;
        background: var(--primary);
        color: white;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
    }
    
    /* Hero Section */
    .hero-section {
        position: relative;
        min-height: 80vh;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        padding: 40px 20px;
    }
    
    .hero-bg {
        position: absolute;
        inset: 0;
        background: linear-gradient(rgba(252, 249, 248, 0.4), rgba(252, 249, 248, 0.4)), 
                    url('https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1920&q=80');
        background-size: cover;
        background-position: center;
        filter: blur(4px);
        transform: scale(1.05);
    }
    
    .hero-content {
        position: relative;
        z-index: 1;
        max-width: 800px;
        text-align: center;
    }
    
    .hero-title {
        font-family: 'Outfit', sans-serif;
        font-size: 56px;
        font-weight: 700;
        color: var(--primary);
        margin-bottom: 16px;
        line-height: 1.1;
    }
    
    .hero-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 18px;
        color: var(--on-surface-variant);
        margin-bottom: 32px;
        line-height: 1.5;
    }
    
    /* Status Badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 20px;
    }
    
    .status-online {
        background: rgba(46, 125, 50, 0.15);
        color: #2e7d32;
        border: 1px solid rgba(46, 125, 50, 0.3);
    }
    
    .status-offline {
        background: rgba(239, 108, 0, 0.15);
        color: #ef6c00;
        border: 1px solid rgba(239, 108, 0, 0.3);
    }
    
    /* Bottom Navigation */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(252, 249, 248, 0.8);
        backdrop-filter: blur(20px);
        border-top: 1px solid rgba(143, 111, 110, 0.2);
        padding: 12px 16px 32px;
        display: flex;
        justify-content: space-around;
        align-items: center;
        z-index: 100;
    }
    
    .dark .bottom-nav {
        background: rgba(27, 27, 27, 0.8);
    }
    
    .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        color: var(--on-surface-variant);
        text-decoration: none;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .nav-item.active {
        color: var(--primary);
    }
    
    .nav-item:hover {
        color: var(--primary);
    }
    
    .nav-icon {
        font-size: 24px;
    }
    
    .nav-label {
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    
    /* Loading Skeleton */
    .skeleton {
        background: linear-gradient(90deg, var(--surface-container) 25%, var(--surface-container-high) 50%, var(--surface-container) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite linear;
        border-radius: 8px;
    }
    
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    
    /* Animations */
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    .animate-float {
        animation: float 3s ease-in-out infinite;
    }
    
    /* Filter Chips */
    .filter-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.05em;
        white-space: nowrap;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .filter-chip.active {
        background: var(--primary);
        color: var(--on-primary);
    }
    
    .filter-chip.inactive {
        background: var(--surface-container-high);
        color: var(--on-surface-variant);
        border: 1px solid var(--outline-variant);
    }
    
    .filter-chip:hover {
        transform: scale(1.05);
    }
    
    /* Hide Streamlit Default Elements */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--surface-container);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--outline-variant);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--outline);
    }
    
    /* Streamlit Button Customizations */
    button[data-testid="baseButton-secondary"] {
        background-color: var(--surface-container) !important;
        color: var(--primary) !important;
        border: 1px solid var(--outline-variant) !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    button[data-testid="baseButton-secondary"]:hover {
        background-color: var(--surface-variant) !important;
        border-color: var(--primary) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# (Main execution block moved to the end of the file to ensure functions are defined first)

def get_cuisine_image(cuisine: str) -> str:
    """Return a curated high-quality Unsplash image URL based on the cuisine."""
    cuisine_lower = cuisine.lower()
    images = {
        "italian": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&h=300&fit=crop",
        "chinese": "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=400&h=300&fit=crop",
        "north indian": "https://images.unsplash.com/photo-1585938338392-50a5d22b6c7d?w=400&h=300&fit=crop",
        "south indian": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=400&h=300&fit=crop",
        "continental": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop",
        "mexican": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=400&h=300&fit=crop",
        "desserts": "https://images.unsplash.com/photo-1551024601-bec78aea704b?w=400&h=300&fit=crop",
        "cafe": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=400&h=300&fit=crop",
        "beverages": "https://images.unsplash.com/photo-1497534446932-c925b458314e?w=400&h=300&fit=crop",
    }
    for key, url in images.items():
        if key in cuisine_lower:
            return url
    return "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&h=300&fit=crop"


def display_welcome_banner():
    """Display a premium welcome banner/hero card in the content area."""
    st.markdown(textwrap.dedent("""
        <div style="background: linear-gradient(135deg, rgba(255,255,255,0.7), rgba(246,243,242,0.7)); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 40px; text-align: center; margin-bottom: 24px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);">
            <div style="font-size: 64px; margin-bottom: 16px; animation: float 3s ease-in-out infinite;" class="animate-float">🍕</div>
            <h2 style="font-family: 'Outfit', sans-serif; font-size: 36px; font-weight: 700; color: #b7122a; margin-top: 0; margin-bottom: 12px;">Welcome to CraveAI</h2>
            <p style="font-family: 'Inter', sans-serif; font-size: 16px; color: #5b403f; max-width: 500px; margin: 0 auto 24px; line-height: 1.6;">
                Your personal Zomato AI dining curator. Tailor your location, craving, budget, and vibe on the left, and let us cook up your perfect recommendations.
            </p>
            <div style="display: flex; justify-content: center; gap: 16px; font-family: 'Inter', sans-serif; font-size: 14px; color: #8f6f6e; font-weight: 500;">
                <div style="display: flex; align-items: center; gap: 6px;">
                    <span>📍</span> <span>Hyper-Local</span>
                </div>
                <span>•</span>
                <div style="display: flex; align-items: center; gap: 6px;">
                    <span>✨</span> <span>AI-Driven Insights</span>
                </div>
                <span>•</span>
                <div style="display: flex; align-items: center; gap: 6px;">
                    <span>🍱</span> <span>Custom Craving Match</span>
                </div>
            </div>
        </div>
    """).strip(), unsafe_allow_html=True)


def display_results(result, summary, used_fallback):
    """Display restaurant recommendations with premium glassmorphism cards."""
    
    # Display Summary Title
    if summary:
        st.markdown(f"<h2 style='font-family: Outfit, sans-serif; font-size: 32px; font-weight: 600; color: #1b1b1b; margin-bottom: 16px;'>{summary}</h2>", unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='font-family: Outfit, sans-serif; font-size: 32px; font-weight: 600; color: #1b1b1b; margin-bottom: 16px;'>Recommended for you:</h2>", unsafe_allow_html=True)
    
    if used_fallback:
        st.warning("⚠️ The AI reasoning server was offline or busy. Showing rating-sorted matching restaurants.")
    
    recommendations = result.get("recommendations", [])
    
    # Display cards in a grid
    if not recommendations:
        st.info("ℹ️ No restaurants matched your specific criteria.")
    else:
        # Add insights section with rating distribution
        display_insights_section(recommendations)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Create columns for card grid
        cols = st.columns(min(2, len(recommendations)))
        
        for idx, rec in enumerate(recommendations):
            col_idx = idx % len(cols)
            with cols[col_idx]:
                rating = rec.get("rating", 0.0)
                rank = rec.get("rank", idx + 1)
                
                # Get premium curated cuisine image URL
                cuisine = rec.get('cuisine', 'restaurant')
                image_url = get_cuisine_image(cuisine)
                
                premium_badge_html = (
                    '<div style="position: absolute; top: 16px; left: 16px; z-index: 10;">'
                    '<span style="background: #b7122a; color: white; padding: 4px 12px; border-radius: 8px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; box-shadow: 0 4px 12px rgba(183, 18, 42, 0.3);">'
                    'Premium Choice'
                    '</span>'
                    '</div>'
                ) if rank == 1 else ""

                card_html = (
                    '<div class="restaurant-card" style="margin-bottom: 24px; position: relative;">'
                    '<div style="position: relative; height: 240px; overflow: hidden;">'
                    f'<img src="{image_url}" alt="{rec.get("name")}" class="restaurant-image">'
                    '<div class="rating-badge" style="position: absolute; top: 16px; right: 16px; background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(10px); padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 13px; display: flex; align-items: center; gap: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); z-index: 10;">'
                    '<span class="material-symbols-outlined" style="font-size: 16px; color: #b7122a; font-variation-settings: \'FILL\' 1;">star</span>'
                    f'<span>{rating:.1f}</span>'
                    '</div>'
                    f'{premium_badge_html}'
                    '</div>'
                    '<div style="padding: 24px; display: flex; flex-direction: column; gap: 16px;">'
                    '<div style="display: flex; justify-content: space-between; align-items: flex-start;">'
                    '<div>'
                    f'<h3 class="restaurant-name" style="font-family: \'Outfit\', sans-serif; font-size: 20px; font-weight: 700; color: #1b1b1b; margin: 0 0 4px 0;">{rec.get("name")}</h3>'
                    '<p style="font-family: \'Inter\', sans-serif; font-size: 14px; color: #5b403f; margin: 0; display: flex; align-items: center; gap: 4px;">'
                    '<span class="material-symbols-outlined" style="font-size: 16px; color: #8f6f6e;">location_on</span>'
                    f'<span>{rec.get("location")}</span>'
                    '</p>'
                    '</div>'
                    f'<span class="cost-badge" style="font-family: \'Outfit\', sans-serif; font-size: 18px; font-weight: 700; color: #b7122a;">{rec.get("estimated_cost")}</span>'
                    '</div>'
                    f'<div style="font-family: \'Inter\', sans-serif; font-size: 14px; color: #5b403f; font-weight: 500;">{rec.get("cuisine")}</div>'
                    '<div class="ai-explanation" style="background: rgba(183, 18, 42, 0.05); border: 1px solid rgba(183, 18, 42, 0.1); border-radius: 12px; padding: 12px; display: flex; align-items: flex-start; gap: 8px;">'
                    '<span class="material-symbols-outlined" style="font-size: 18px; color: #b7122a; font-variation-settings: \'FILL\' 1;">auto_awesome</span>'
                    '<p style="font-family: \'Inter\', sans-serif; font-size: 12px; color: #5b403f; margin: 0; line-height: 1.5;">'
                    f'<span style="color: #b7122a; font-weight: 700;">AI Reason:</span> {rec.get("explanation")}'
                    '</p>'
                    '</div>'
                    '<div style="display: flex; justify-content: space-between; align-items: center; padding-top: 8px; border-top: 1px solid rgba(143,111,110,0.1);">'
                    '<div style="display: flex; align-items: center;">'
                    '<img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=60&h=60&fit=crop" style="width: 28px; height: 28px; border-radius: 50%; border: 2px solid white; margin-right: -8px; object-fit: cover;">'
                    '<img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=60&h=60&fit=crop" style="width: 28px; height: 28px; border-radius: 50%; border: 2px solid white; margin-right: -8px; object-fit: cover;">'
                    '<div style="width: 28px; height: 28px; border-radius: 50%; border: 2px solid white; background: #e5e2e1; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; color: #5b403f;">+12</div>'
                    '</div>'
                    '<button style="background: none; border: none; padding: 0; font-family: \'Inter\', sans-serif; font-size: 13px; font-weight: 700; color: #b7122a; display: flex; align-items: center; gap: 4px; cursor: pointer;">'
                    '<span>Expand for Details</span>'
                    '<span class="material-symbols-outlined" style="font-size: 16px;">keyboard_arrow_down</span>'
                    '</button>'
                    '</div>'
                    '</div>'
                    '</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)


def display_loading_skeleton():
    """Display loading skeleton cards while fetching recommendations."""
    st.markdown("<h2 style='font-family: Outfit, sans-serif; font-size: 32px; font-weight: 600; color: #1b1b1b; margin-bottom: 16px;'>Finding your perfect match...</h2>", unsafe_allow_html=True)
    
    cols = st.columns(2)
    for col in cols:
        with col:
            skeleton_html = (
                '<div class="restaurant-card" style="margin-bottom: 24px;">'
                '<div style="position: relative; height: 200px; overflow: hidden;">'
                '<div class="skeleton" style="width: 100%; height: 100%;"></div>'
                '</div>'
                '<div style="padding: 20px;">'
                '<div class="skeleton" style="width: 70%; height: 24px; margin-bottom: 8px; border-radius: 4px;"></div>'
                '<div class="skeleton" style="width: 40%; height: 16px; margin-bottom: 12px; border-radius: 4px;"></div>'
                '<div style="display: flex; justify-content: space-between; margin: 12px 0;">'
                '<div class="skeleton" style="width: 30%; height: 14px; border-radius: 4px;"></div>'
                '<div class="skeleton" style="width: 20%; height: 18px; border-radius: 4px;"></div>'
                '</div>'
                '<div class="skeleton" style="width: 100%; height: 60px; border-radius: 8px;"></div>'
                '</div>'
                '</div>'
            )
            st.markdown(skeleton_html, unsafe_allow_html=True)


def display_insights_section(recommendations):
    """Display insights section with rating distribution and statistics."""
    
    ratings = [rec.get("rating", 0.0) for rec in recommendations]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
    total = len(ratings)
    
    rating_dist = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for r in ratings:
        if r >= 4.5:
            rating_dist[5] += 1
        elif r >= 3.5:
            rating_dist[4] += 1
        elif r >= 2.5:
            rating_dist[3] += 1
        elif r >= 1.5:
            rating_dist[2] += 1
        else:
            rating_dist[1] += 1
            
    max_count = max(rating_dist.values()) if rating_dist else 1
    
    header_html = (
        '<div class="glass-card" style="padding: 24px; margin-bottom: 24px;">'
        '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">'
        '<h3 style="font-family: Outfit, sans-serif; font-size: 24px; font-weight: 600; color: #1b1b1b; margin: 0;">Community Ratings</h3>'
        '<div style="display: flex; align-items: center; gap: 8px; color: #b7122a;">'
        '<span class="material-symbols-outlined" style="font-size: 24px; font-variation-settings: \'FILL\' 1;">star</span>'
        f'<span style="font-weight: 700; font-size: 18px;">{avg_rating:.1f}</span>'
        f'<span style="font-size: 14px; color: #5b403f;">({total} reviews)</span>'
        '</div>'
        '</div>'
        '<div style="display: flex; align-items: flex-end; justify-content: space-between; gap: 8px; height: 120px; padding: 0 8px;">'
    )
    
    bars_html = []
    for star in [5, 4, 3, 2, 1]:
        count = rating_dist[star]
        bar_height = (count / max_count * 100) if max_count > 0 else 0
        
        bar_html = (
            '<div style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8px; position: relative; height: 100%; justify-content: flex-end;">'
            f'<div style="position: absolute; top: -32px; left: 50%; transform: translateX(-50%); background: #1b1b1b; color: #fcf9f8; font-size: 10px; padding: 4px 8px; border-radius: 4px; opacity: 0; transition: opacity 0.3s; pointer-events: none;" class="hover-tooltip">{count}</div>'
            f'<div style="width: 100%; background: #e5e2e1; border-radius: 8px 8px 0 0; height: {bar_height}%; transition: all 0.3s ease; cursor: pointer;" onmouseover="this.previousElementSibling.style.opacity=\'1\'" onmouseout="this.previousElementSibling.style.opacity=\'0\'">'
            '<div style="width: 100%; height: 100%; background: #b7122a; border-radius: 8px 8px 0 0; opacity: 0.6;"></div>'
            '</div>'
            f'<span style="font-size: 10px; color: #5b403f;">{star}★</span>'
            '</div>'
        )
        bars_html.append(bar_html)
        
    full_html = header_html + "".join(bars_html) + "</div></div>"
    st.markdown(full_html, unsafe_allow_html=True)


# ----------------------------------------------------
# Bottom Navigation
# ----------------------------------------------------
st.markdown("""
<div class="bottom-nav">
    <div class="nav-item active">
        <span class="nav-icon">🏠</span>
        <span class="nav-label">Home</span>
    </div>
    <div class="nav-item">
        <span class="nav-icon">🔍</span>
        <span class="nav-label">Search</span>
    </div>
    <div class="nav-item">
        <span class="nav-icon">❤️</span>
        <span class="nav-label">Favorites</span>
    </div>
    <div class="nav-item">
        <span class="nav-icon">🤖</span>
        <span class="nav-label">AI Chat</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# App State & API Detection
# ----------------------------------------------------
api_online = check_api_status()

# Dark mode state
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# Apply dark mode class if enabled
if st.session_state.dark_mode:
    st.markdown('<script>document.documentElement.classList.add("dark")</script>', unsafe_allow_html=True)

# ----------------------------------------------------
# Top App Bar
# ----------------------------------------------------
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <div style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #b7122a, #db313f); display: flex; align-items: center; justify-content: center; color: white; font-size: 24px;">🍕</div>
        <h1 style="font-family: 'Outfit', sans-serif; font-size: 24px; font-weight: 700; color: #b7122a; margin: 0;">CraveAI</h1>
    </div>
    """, unsafe_allow_html=True)

with col2:
    if st.button("🌙" if not st.session_state.dark_mode else "☀️", key="dark_mode_toggle", help="Toggle dark mode"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# Connection Status Badge
if api_online:
    st.markdown('<div class="status-badge status-online">🟢 Connected to Backend API</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="status-badge status-offline">🟠 Running In-Process (Backend API Offline)</div>', unsafe_allow_html=True)

# ----------------------------------------------------
# Main Content Area
# ----------------------------------------------------
main_container = st.container()

with main_container:
    # Initialize session state variables
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False
        
    # Load dataset hints
    cities, location_options, cuisines, budget_tiers = load_dataset_hints(api_online)
    
    # 2-Column Split Layout
    col_left, col_right = st.columns([1, 2], gap="large")
    
    with col_left:
        st.markdown("""
        <div style="background: rgba(183, 18, 42, 0.03); border: 1px solid rgba(183, 18, 42, 0.08); border-radius: 12px; padding: 16px; margin-bottom: 20px;">
            <h3 style="font-family: Outfit, sans-serif; font-size: 20px; font-weight: 600; color: #b7122a; margin: 0 0 4px 0;">Search Filters</h3>
            <p style="font-family: Inter, sans-serif; font-size: 13px; color: #5b403f; margin: 0;">Tailor your food search</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Location Selection
        location = st.selectbox(
            "📍 Select Location (Neighborhood/City)",
            options=location_options,
            index=location_options.index("Bangalore") if "Bangalore" in location_options else 0,
            key="location_select",
            help="Choose a specific neighborhood (e.g., 'Indiranagar, Bangalore') or select a city-wide search."
        )
        
        # Cuisine Selection
        selected_cuisine = st.selectbox(
            "🍕 Select Cuisine (Craving)",
            options=["Any"] + cuisines,
            index=0,
            key="cuisine_select"
        )
        
        # Budget Tier
        budget = st.radio(
            "💰 Select Budget Level",
            options=["low", "medium", "high"],
            index=1,
            format_func=lambda x: x.capitalize(),
            horizontal=True,
            key="budget_select"
        )
        
        # Minimum Rating
        min_rating = st.slider(
            "⭐ Minimum Rating",
            min_value=0.0,
            max_value=5.0,
            value=4.0,
            step=0.1,
            key="rating_slider"
        )
        
        # Additional Preferences
        additional_prefs = st.text_area(
            "✍️ Additional Vibes & Preferences",
            placeholder="e.g., rooftop, live music, fast service, family friendly",
            key="additional_prefs",
            help="Describe the atmosphere, specific dishes, or amenities you're looking for."
        )
        
        # Top K Slider
        top_k = st.slider(
            "🔢 Number of Suggestions",
            min_value=1,
            max_value=10,
            value=5,
            key="top_k_slider"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Action Buttons
        find_recommendations = st.button("✨ Find Recommendations", type="primary", use_container_width=True)
        
        if st.button("🔄 Reset Search", use_container_width=True):
            st.session_state.show_results = False
            if 'recommendations' in st.session_state:
                del st.session_state.recommendations
            st.rerun()
            
    with col_right:
        # Trigger Action
        if find_recommendations:
            # Display loading skeleton immediately on click
            display_loading_skeleton()
            
            cuisine_value = "Any" if selected_cuisine == "Any" else selected_cuisine
            additional_list = [t.strip() for t in additional_prefs.split(",") if t.strip()]
            
            preferences_payload = {
                "location": location,
                "budget": budget,
                "cuisine": cuisine_value,
                "min_rating": min_rating,
                "additional_preferences": additional_list,
                "top_k": top_k
            }
            
            with st.spinner("Cooking up your personalized recommendations..."):
                result = get_recommendations(preferences_payload, api_online)
                
            if not result.get("success", False):
                st.error(f"⚠️ Recommendation Failed: {result.get('error', 'Unknown Error')}")
            else:
                st.session_state.recommendations = result
                st.session_state.summary = result.get("summary")
                st.session_state.used_fallback = result.get("used_fallback", False)
                st.session_state.show_results = True
                st.rerun()
                
        elif st.session_state.get('show_results') and 'recommendations' in st.session_state:
            # Display Results and Stats
            display_results(
                st.session_state.recommendations,
                st.session_state.summary,
                st.session_state.used_fallback
            )
        else:
            # Show Welcome Screen
            display_welcome_banner()
