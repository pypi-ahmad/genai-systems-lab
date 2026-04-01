FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ shared/
COPY crew-*/ ./
COPY genai-*/ ./
COPY lg-*/ ./
COPY .env* ./

EXPOSE 8000

CMD ["uvicorn", "shared.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
