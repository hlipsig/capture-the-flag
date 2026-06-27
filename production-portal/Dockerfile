FROM registry.access.redhat.com/ubi9/python-311:latest

USER root

# Install app dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .

# Create non-root user
RUN useradd -u 1001 -r -g 0 -d /app -s /sbin/nologin appuser && \
    chown -R 1001:0 /app && \
    chmod -R g=u /app

USER 1001

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Run the app
CMD ["python", "app.py"]
