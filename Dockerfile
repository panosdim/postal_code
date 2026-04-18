FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py .
COPY index.html .
COPY data.sqlite .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]