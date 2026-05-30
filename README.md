# Zomato AI — Restaurant Recommendation System

AI-powered restaurant recommendations using the Zomato Hugging Face dataset and LLM reasoning.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Phase 1: Data ingestion

Load and preprocess the dataset:

```bash
PYTHONPATH=. python3 -m app.data
```

Uses cache at `data/cache/restaurants.parquet` after the first download. Set `FORCE_REFRESH_DATASET=true` in `.env` to re-fetch from Hugging Face.

### Use in code

```python
from app.data.repository import RestaurantRepository

repo = RestaurantRepository.from_cache_or_dataset()
print(repo.count, repo.get_cities()[:5])
bangalore = repo.get_by_city("Bangalore")
```

## Phase 3: LLM integration

```python
from app.data.repository import RestaurantRepository
from app.domain.filter import FilterService
from app.domain.models import UserBudget, UserPreferences
from app.llm.engine import RecommendationEngine
from app.llm.client import get_llm_client

repo = RestaurantRepository.from_cache_or_dataset()
engine = RecommendationEngine(
    filter_service=FilterService(repo),
    llm_client=get_llm_client(use_mock=True),  # set False + LLM_API_KEY for Groq
)
result = engine.recommend(UserPreferences(
    location="Bangalore",
    budget=UserBudget.MEDIUM,
    cuisine="Italian",
    min_rating=4.0,
    top_k=3,
))
print(result.summary, result.recommendations)
```

Smoke test (mock LLM, no API key):

```bash
PYTHONPATH=. python3 -m app.llm --mock --top-k 3
```

With Groq, set `LLM_API_KEY` (or `GROQ_API_KEY`) from [console.groq.com](https://console.groq.com/keys) in `.env` and omit `--mock`.

## Phase 2: Filter service

```python
from app.data.repository import RestaurantRepository
from app.domain.filter import FilterService
from app.domain.models import UserBudget, UserPreferences

repo = RestaurantRepository.from_cache_or_dataset()
service = FilterService(repo)

prefs = UserPreferences(
    location="Bangalore",
    budget=UserBudget.MEDIUM,
    cuisine="Italian",
    min_rating=4.0,
)
result = service.apply(prefs)
print(result.candidates, result.message, result.suggestions)
```

CLI demo:

```bash
PYTHONPATH=. python3 -m app.domain
```

## Tests

```bash
PYTHONPATH=. python3 -m pytest tests/ -v
```

## Phase 6: Testing & QA Documentation

### Performance Metrics
*   **Repository Ingestion:** ~11,740 restaurants loaded from cached Parquet store in **~0.5s**.
*   **Deterministic Filtering:** Candidate filtering completes in **~1.5ms to 4ms** (well within the 100ms budget).
*   **LLM Latency Expectations:** Typical Groq Llama-3.3-70b inference latency is **~1.5s to 3.0s**.

### Manual QA Scenarios (Verify in UI)
1.  **Scenario 1: High-End Italian in Bangalore**
    *   📍 Select Location: `Bangalore`
    *   🍕 Select Cuisine: `Italian`
    *   💰 Select Budget Level: `High`
    *   ⭐ Minimum Rating: `4.2`
    *   ✍️ Vibes & Details: `rooftop, outdoor seating`
2.  **Scenario 2: Low-Budget Quick Chinese in Bangalore**
    *   📍 Select Location: `Bangalore`
    *   🍕 Select Cuisine: `Chinese`
    *   💰 Select Budget Level: `Low`
    *   ⭐ Minimum Rating: `3.5`
    *   ✍️ Vibes & Details: `quick service, casual`
3.  **Scenario 3: No Match Filter Relaxation**
    *   📍 Select Location: `Bangalore`
    *   🍕 Select Cuisine: `Mexican`
    *   💰 Select Budget Level: `Low`
    *   ⭐ Minimum Rating: `4.9`
    *   *Expected UX Result:* Intercepts at the filter level and displays suggestions to relax the filters instead of calling the LLM.

## Docker & Deployment

The application is containerized and can be run in production or staging environments:

### 1. Build Docker Image
```bash
docker build -t zomato-ai .
```

### 2. Run Container
Run the FastAPI backend + React UI on port 8000:
```bash
docker run -p 8000:8000 --env-file .env zomato-ai
```

Or run the Streamlit UI on port 8501:
```bash
docker run -p 8501:8501 --env-file .env zomato-ai streamlit run app/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

## Project docs

- [`context.md`](context.md) — project summary
- [`architecture.md`](architecture.md) — system design
- [`implementation-plan.md`](implementation-plan.md) — phased build plan
- [`edge-cases.md`](edge-cases.md) — edge-case handling
