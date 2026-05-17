FROM pytorch/pytorch:2.11.0-cuda13.0-cudnn9-runtime

WORKDIR /workspace

# STT often needs ffmpeg or libsndfile
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
ENV PIP_BREAK_SYSTEM_PACKAGES=1
RUN pip install --no-cache-dir .

COPY serv/ ./serv/

# Run the STT service
CMD ["python", "-m", "serv.stt.main"]