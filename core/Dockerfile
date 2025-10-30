FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv sync
RUN uv sync --frozen --no-cache

# Copy project files
COPY . .

# Create media directory
RUN mkdir -p media

# Expose port
EXPOSE 8000

# Use uv run to execute with virtual environment
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
