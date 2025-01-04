# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Copy the root directory contents into the container at /app
COPY ../ /app


# Install any needed packages specified in requirements.txt
RUN cd /app
RUN pip install --no-cache-dir -r requirements.txt
# Make speccheck.py executable
ENV PATH="/app:${PATH}"
RUN chmod +x speccheck.py
CMD ["python", "speccheck.py"]