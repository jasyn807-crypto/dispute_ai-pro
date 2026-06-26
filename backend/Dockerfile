FROM python:3.10-slim

WORKDIR /app

# Install system dependencies needed for compiling certain python libs (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Run database seeder on container start to make sure db is ready, then run the app
CMD python seed_data.py && python run.py
