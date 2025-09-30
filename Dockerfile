# Multi-stage build for efficient image
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
WORKDIR /app
COPY requirements.txt .

# Create venv and install packages using pip (more reliable in Docker)
RUN python -m venv .venv && \
    .venv/bin/pip install --upgrade pip && \
    .venv/bin/pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

# Install runtime dependencies including OpenCV requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    imagemagick \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    libglib2.0-0 \
    libxrender1 \
    libxfixes3 \
    libxi6 \
    libxcb1 \
    libxau6 \
    libxdmcp6 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy Python environment from builder
COPY --from=builder /app/.venv /app/.venv

# Set up working directory
WORKDIR /app

# Copy application code
COPY . .

# Set model directory (models will download on first use)
ENV U2NET_HOME=/root/.u2net

# Set Python path
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

# Create directories for input/output
RUN mkdir -p /data/input /data/output /data/processed

# Default environment variables
ENV BACKGROUND_REMOVAL_METHOD=rembg
ENV REMBG_MODEL=bria-rmbg
ENV QUALITY_PRESET=ultra
ENV MAX_CONCURRENT_IMAGES=3

# Expose Streamlit port
EXPOSE 8501

# Default command (can be overridden)
CMD ["streamlit", "run", "streamlit_app.py", "--server.address", "0.0.0.0"]