# Use official PyTorch image with PyTorch 2.5.1 and CUDA 12.4 runtime support
FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

# Set working directory inside the container
WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered output for real-time logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GRADIO_SERVER_NAME="0.0.0.0" \
    GRADIO_SERVER_PORT=7860

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies list and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose Gradio default port
EXPOSE 7860

# Command to run the application
CMD ["python", "-m", "src.app"]