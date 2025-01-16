# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory's files into the container
COPY . /app

# Install necessary Python dependencies
RUN pip install --no-cache-dir autopep8 flake8 jupyter

# Expose the Jupyter Notebook port
EXPOSE 8888

# Run Jupyter Notebook in a Colab-like environment
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
