FROM pytorch/pytorch:2.11.0-cuda13.0-cudnn9-runtime
# 1. Fix the "No Output" freeze (Log Buffering)
ENV PYTHONUNBUFFERED=1
# 2. Fix the Silero "y/N" freeze (Pre-trust the repo)
RUN mkdir -p /root/.cache/torch/hub && \
    echo '["snakers4/silero-models"]' > /root/.cache/torch/hub/trusted_repositories.json
WORKDIR /workspace
# Install system dependencies (common for audio/ML apps)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
# Copy dependency files first for caching
COPY pyproject.toml .
ENV PIP_BREAK_SYSTEM_PACKAGES=1
RUN pip install --no-cache-dir .
# Copy the source code and resources
COPY app/ ./app/
COPY res/ ./res/
# Note: 'data' folder is usually handled via volumes, not baked into the image
# Run the main app
CMD ["sh", "-c", "yes | python -m app.main"]
#`yes` to bypass (y/N)? when downloading Silero TTS