FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Install the package
RUN pip install -e .

# Set Python path
ENV PYTHONPATH=/app/src

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Start command (Railway will use Start Command from settings, this is fallback)
# Use sh -c to properly expand $PORT environment variable
CMD sh -c "python -m uvicorn petcare_advisor.main:app --host 0.0.0.0 --port ${PORT:-8000}"

