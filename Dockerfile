FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Hugging Face Space default port 7860
EXPOSE 7860

# Run Flask application
CMD ["python", "app.py"]
