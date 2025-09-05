FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY services/payment-service/requirements.txt ./requirements.txt

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY ../../shared ./shared
COPY ../../mode.py ./mode.py

# Copy the application code to the working directory
COPY services/payment-service/ .

RUN ls -la /app/

# Expose the port on which the application will run
EXPOSE 8003

# Run the FastAPI application using uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]