# 1. Use an official Python runtime as a parent image
FROM python:3.11-slim

# 2. Set the working directory in the container
WORKDIR /app

# 3. Install uv
RUN pip install uv

# 4. Copy the requirements file into the container at /app
COPY requirements.txt .

# 5. Install any needed packages specified in requirements.txt
RUN uv pip install --no-cache-dir --system -r requirements.txt

# 6. Copy the rest of the application's code from the host to the image
COPY ./app /app/app

# 7. Expose the port the app runs on
EXPOSE 8000

# 8. Define the command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
