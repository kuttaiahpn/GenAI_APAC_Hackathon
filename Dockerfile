# Use the official Python slim image for a smaller, secure baseline
FROM python:3.11-slim

# Prevent Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

# Create and switch to a non-root user for security
RUN groupadd -r mcp && useradd -r -g mcp mcp

WORKDIR /app

# Install system dependencies required for psycopg/asyncpg or compilation if any
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application payload
COPY backend/ ./backend/
COPY documents/ ./documents/

# Optional: Map AlloyDB Auth explicit variables (handled by Cloud Run Secrets normally)
# ENV DB_PASSWORD=my_secure_password

# Assign app directory ownership to non-root user
RUN chown -R mcp:mcp /app

# Switch to the non-root user
USER mcp

# Google Cloud Run expects services to listen on port 8080
EXPOSE 8080

# Execute FastAPI via Uvicorn targeting our mcp_server.py implementation
# The backend folder acts as a module implicitly.
CMD ["uvicorn", "backend.mcp_server:app", "--host", "0.0.0.0", "--port", "8080"]
