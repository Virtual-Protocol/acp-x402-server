# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# Copy x402 library first (for better caching)
COPY python/x402 /app/python/x402

# Install x402 package
RUN cd /app/python/x402 && uv pip install -e .

# Copy FastAPI example
COPY examples/python/servers/fastapi /app/examples/python/servers/fastapi

# Install FastAPI example dependencies
WORKDIR /app/examples/python/servers/fastapi
RUN uv pip install fastapi uvicorn python-dotenv pyjwt cryptography cdp-sdk httpx

# Expose port
EXPOSE 4021

# Health check (use curl for simplicity, or install it if needed)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4021/premium/content').read()"

# Run the application
CMD ["python", "main.py"]

