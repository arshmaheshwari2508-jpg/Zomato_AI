# Project Context: AI-Powered Restaurant Recommendation System

## Overview

Build an **AI-powered restaurant recommendation service** inspired by Zomato. The system combines **structured restaurant data** with a **Large Language Model (LLM)** to deliver personalized, human-like suggestions based on user preferences.

## Objective

Design and implement an application that:

1. Accepts user preferences (location, budget, cuisine, ratings, and more)
2. Uses a real-world restaurant dataset
3. Leverages an LLM for personalized, natural-language recommendations
4. Presents clear, useful results to the user

## Data Source

| Item | Detail |
|------|--------|
| **Dataset** | Zomato restaurant data on Hugging Face |
| **URL** | https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation |
| **Relevant fields** | Restaurant name, location, cuisine, cost, rating, and related attributes |

## System Workflow

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face
- Extract fields: restaurant name, location, cuisine, cost, rating, etc.

### 2. User Input

Collect preferences including:

| Preference | Examples |
|------------|----------|
| **Location** | Delhi, Bangalore |
| **Budget** | low, medium, high |
| **Cuisine** | Italian, Chinese |
| **Minimum rating** | Numeric threshold |
| **Additional** | family-friendly, quick service, etc. |

### 3. Integration Layer

- Filter and prepare restaurant data matching user input
- Pass structured results into an LLM prompt
- Design prompts so the LLM can reason over and rank options

### 4. Recommendation Engine

Use the LLM to:

- Rank restaurants
- Explain why each recommendation fits the user
- Optionally summarize the top choices

### 5. Output Display

Present top recommendations in a user-friendly format with:

- Restaurant name
- Cuisine
- Rating
- Estimated cost
- AI-generated explanation

## Architecture (High Level)

```
User Preferences → Data Filter → Structured Candidates → LLM Prompt → Ranked Recommendations → UI
        ↑                              ↑
   Hugging Face Dataset (preprocessed)
```

## Key Technical Considerations

- **Hybrid approach**: deterministic filtering on structured data before LLM reasoning (cost, location, cuisine, rating)
- **Prompt design**: structured context for the LLM (filtered restaurant list + user preferences) to enable ranking and explanations
- **Output quality**: balance factual fields from the dataset with LLM-generated narrative explanations
- **UX**: results should be scannable (name, cuisine, rating, cost) with optional deeper AI rationale

## Success Criteria

- Users can specify preferences and receive relevant restaurant suggestions
- Recommendations are grounded in real dataset records
- LLM adds value through ranking, explanation, and optional summarization
- Output is clear, readable, and actionable

## Source Document

Full problem statement: `Docs/ProblemStatement.txt`
