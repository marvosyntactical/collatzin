FROM python:3.11-slim

# Basic OS hygiene
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY collatz_dash.py .

# Fly’s routing layer looks at PORT
ENV PORT=8050
EXPOSE 8050

CMD ["python", "collatz_dash.py"]
