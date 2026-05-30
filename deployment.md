# Streamlit Deployment Guide

This document explains how to deploy the **CraveAI Zomato Recommendation System** on **Streamlit Community Cloud**.

---

## 1. Prerequisites & Preparation

1. **GitHub Repository**:
   - Create a public repository on GitHub and push the codebase.
   - Ensure the following files and directories are excluded from version control via your `.gitignore`:
     ```text
     .venv/
     .env
     data/cache/
     __pycache__/
     .pytest_cache/
     ```
     *(Do **not** commit `data/cache/restaurants.parquet` or `.env` as the parquet is too large for GitHub and the `.env` contains credentials.)*

2. **In-Process Fallback Support**:
   - The application automatically falls back to in-process execution when the FastAPI backend is offline. You do not need to host a separate API backend; Streamlit Community Cloud will run the recommendation engine directly inside the Streamlit instance.

---

## 2. Deploying on Streamlit Community Cloud

1. **Sign In**:
   - Visit [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.

2. **Set Up a New Application**:
   - Click the **"New app"** button.
   - Choose your repository, the deployment branch (e.g. `main`), and set the entry file path:
     * **Main file path:** `app/ui/streamlit_app.py`
   - Click **"Deploy!"**

3. **Configure Environment Variables (Secrets)**:
   - In the Streamlit app console, click the **Settings** gear icon.
   - Click the **Secrets** tab.
   - Paste the following environment keys in TOML format:
     ```toml
     LLM_PROVIDER = "groq"
     LLM_API_KEY = "gsk_YOUR_REAL_GROQ_API_KEY"
     LLM_MODEL = "llama-3.3-70b-versatile"
     
     # Optional:
     HF_DATASET_NAME = "ManikaSaini/zomato-restaurant-recommendation"
     FORCE_REFRESH_DATASET = "false"
     MAX_CANDIDATES = 30
     DEFAULT_TOP_K = 5
     ```
   - Click **"Save"**. Streamlit will automatically inject these into the process environment.

---

## 3. Runtime Lifecycle Notes

- **Cold Start Duration**: When the container boots for the first time (or recovers from sleep mode), the application will download the dataset from Hugging Face (`~140MB`). This will take **1 to 2 minutes** on the first visit.
- **Cache Acceleration**: Once downloaded, the preprocessed data is cached locally on the disk, reducing subsequent boot times to **~0.5 seconds**.
- **Inactivity Sleep**: Apps with no traffic for several days will be put to sleep automatically by Streamlit. Visiting the app URL will wake it up and trigger a cold start.
