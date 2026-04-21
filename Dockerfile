# Multi-stage build for FastAPI backend

# Stage 1: Build dependencies
FROM python:3.14-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*


# Install Poetry and plugins
RUN pip install --no-cache-dir poetry
RUN poetry self add poetry-plugin-export

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry export \
    --format requirements.txt \
    --output requirements.txt \
    --without-hashes

# Stage 2: Runtime
FROM python:3.14-slim

WORKDIR /app

# Install runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from builder
COPY --from=builder /app/requirements.txt* ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
