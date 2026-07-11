FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy the project into the image
COPY . /app

# Sync the project into a new environment, using the frozen lockfile
RUN uv sync --frozen --no-dev

# Ensure the installed binary is on the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose port 7860, default for Hugging Face Spaces
EXPOSE 7860

# Run the FastAPI application
CMD sh -c "uvicorn src.roadmap_engine.main:app --host 0.0.0.0 --port ${PORT:-7860}"
