FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements.txt into the working directory
COPY requirements.txt .

# Install the dependencies without caching to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire service package into the working directory
COPY service/ ./service/

# ------------------------------------------------------------
# Create a non-root user called 'theia' and set ownership
# ------------------------------------------------------------
 
# Create theia with password, "non-interactive" fields, and a home directory
RUN adduser --uid 1000 theia

# Change ownership of /app to user theia
RUN chown -R theia:theia /app

# Switch to the theia user
USER theia

# Expose port 8080
EXPOSE 8080

# Run gunicorn when the container starts
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--log-level=info", "service:app"]