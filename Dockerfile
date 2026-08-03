FROM python:3.12-slim

# Hugging Face Spaces (Docker SDK) runs the container as a non-root user (UID 1000).
# Create a matching user and make /app writable by it, otherwise anything that tries
# to write a cache file (sentence-transformers model cache, our embedding cache, ...)
# fails with PermissionError and crashes the app on startup.
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code, owned by the runtime user
COPY --chown=appuser:appuser . .

# Point HOME + all model/vector caches at writable paths under /app instead of the
# default (~/.cache, unwritable for UID 1000 without the setup above).
ENV HOME=/app \
    HF_HOME=/app/.hf-cache \
    SENTENCE_TRANSFORMERS_HOME=/app/.sentence-transformers \
    CHROMA_PERSIST_DIR=/app/.chroma

RUN mkdir -p "$HF_HOME" "$SENTENCE_TRANSFORMERS_HOME" "$CHROMA_PERSIST_DIR" /app/.cache \
    && chown -R appuser:appuser /app

USER appuser

# Expose Hugging Face Space default port 7860
EXPOSE 7860

# Run Flask application
CMD ["python", "app.py"]
