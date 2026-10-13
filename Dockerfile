# Dockerfile for StudyMate Production Deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEPLOY_ENV=production
ENV PORT=8000
ENV HOST=0.0.0.0

# Copy application files
COPY . /app

# Ensure uploads directory exists
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Start production server
CMD ["python", "web_app.py"]
