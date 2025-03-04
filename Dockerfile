# Use a lightweight official Python image
FROM python:3.11-slim

# Set working directory in the container
WORKDIR /app

# Copy requirements and install
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code into the container
COPY . /app/

# Expose the default Flask port
EXPOSE 5000

# Default command: run the downloader, then launch the Flask app
CMD ["bash", "-c", "python foia_downloader.py --max-workers 5 && python app.py"]