FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install CPU-only torch + torchaudio together to avoid version conflicts
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

COPY requirements-deploy.txt .
RUN pip install --no-cache-dir -r requirements-deploy.txt

COPY . .

RUN mkdir -p uploads audio_outputs

# HuggingFace Spaces requires port 7860
EXPOSE 7860

ENV PORT=7860
ENV FLASK_ENV=production
ENV FLASK_DEBUG=false

CMD ["python", "app.py"]
