# Roadmap Engine API

The Roadmap Engine is a backend service powered by **FastAPI** that provides comprehensive learning roadmaps and personalized learning plans for various technical domains (Frontend, Backend, DevOps, AI/ML, and more).

## Features

- **Pre-defined Roadmaps**: Access structured learning paths for dozens of roles and technologies.
- **Topic Granularity**: Fetch detailed topics and subtopics for any given roadmap.
- **AI-Powered Plan Generation**: Generate personalized learning narratives and schedules using LLMs (Groq) based on user's known topics, time availability, and chosen roadmap.
- **Staleness Tracking**: Track when underlying roadmap data has been updated and whether generated plans need refreshing.

##  Tech Stack

- **Framework**: FastAPI
- **Dependency Management**: [uv](https://github.com/astral-sh/uv)
- **AI Integration**: Groq API
- **Deployment**: Docker (configured for Hugging Face Spaces)

##  API Endpoints

Once running, you can interact with the API or view the interactive Swagger documentation at the root URL (which automatically redirects to `/docs`).

- `GET /roadmaps`: Retrieve a list of all supported roadmaps.
- `GET /roadmaps/{roadmap_id}/topics`: Retrieve a flattened structure of all topics and subtopics for a specific roadmap.
- `POST /generate`: Generate a personalized learning plan. Requires a payload with `roadmap_id`, `known_node_ids`, `duration_weeks`, and `hours_per_week`.
- `POST /check-staleness`: Check if a previously generated plan is outdated relative to the latest roadmap definitions.

## Local Development

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd roadmap
   ```

2. **Install dependencies (using `uv`)**:
   ```bash
   uv sync
   ```

3. **Set up Environment Variables**:
   Ensure you have a `.env` file at the root containing your API keys (e.g., `GROQ_API_KEY`).

4. **Run the FastAPI server**:
   ```bash
   uv run uvicorn src.roadmap_engine.main:app --reload
   ```

5. **View the API Docs**:
   Open your browser and navigate to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

##  Hugging Face Spaces Deployment

This repository is fully configured for deployment on **Hugging Face Spaces**. It utilizes the `docker` SDK to seamlessly serve the FastAPI application. 

When pushed to a Space, Hugging Face will automatically:
1. Build the Docker image defined in `Dockerfile`.
2. Install dependencies using `uv`.
3. Serve the application on port `7860`.

When you open the **App** tab on your Hugging Face Space, you will automatically be redirected to the interactive Swagger UI (`/docs`).
