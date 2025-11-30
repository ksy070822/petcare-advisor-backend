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

# Expose port
EXPOSE $PORT

# Start command
CMD ["python", "-m", "uvicorn", "petcare_advisor.main:app", "--host", "0.0.0.0", "--port", "8000"]

