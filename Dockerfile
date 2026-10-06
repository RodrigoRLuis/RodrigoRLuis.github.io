# Use an official lightweight Python image
FROM python:3.14-slim

# Set working directory inside the container
WORKDIR /app

# Copy dependency list first (to leverage Docker cache)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project
COPY . .

# Run linting or tests as part of CI
# (You can override this in the GitHub Actions command)
CMD ["python", "src/main.py"]

