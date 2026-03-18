# Dockerfile for the FastAPI backend (located in this folder)

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY . ./

# Download textblob corpora needed by NRCLex
RUN python -m textblob.download_corpora

# (Optional) Pre-download NLTK data used by the app. This avoids runtime downloads.
RUN python -m nltk.downloader punkt averaged_perceptron_tagger stopwords

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
