FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt   # make sure gunicorn is listed!

COPY . .

# Fly’s proxy will hit whatever $PORT it injects (usually 8080)
ENV PORT=8080
EXPOSE 8080

# ▶️ CRUCIAL ◀️  include the COLON
# CMD gunicorn collatz_dash:server -b :$PORT --workers 3 --timeout 120
CMD ["python3", "collatz_dash.py"]
