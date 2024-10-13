# Use an official lightweight Python image as a base image
FROM python:3.9-slim

#Copy start script to root
COPY start.sh .

# Set the working directory to /app
WORKDIR /app

# Copy only the requirements file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application to the working directory
COPY . .

# Expose the port that the application will run on
EXPOSE 3030

# Expose the port that the weaviate will run on
EXPOSE 8080

# Expose the port that the mongodb will run on
EXPOSE 27017

# Command to run the application with hot reload
CMD ["/bin/bash", "/start.sh"]
