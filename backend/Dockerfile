# backend/Dockerfile
#
# Single-stage build for the FastAPI backend.
#
# Why single-stage (not multi-stage with venv copy)?
#   Copying a venv between Docker stages causes "no such file or directory"
#   at container startup because the venv's script shebang lines contain
#   the builder-stage path (e.g. #!/build/.venv/bin/python3), which does not
#   exist in the runtime stage. pip-installing directly into the system Python
#   avoids this relocation problem entirely.
#
# Local development still uses Poetry (poetry install / poetry run pytest).
# requirements.txt must be kept in sync with pyproject.toml.

FROM python:3.11-slim

# Non-root user for security — containers should not run as root in production
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy requirements first — Docker caches this layer so pip only re-runs
# when requirements.txt changes.
COPY requirements.txt ./

# Install all production dependencies into the system Python.
# --no-cache-dir: skip pip's download cache to keep the image layer small.
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy application source code (copied after pip so code changes don't
# invalidate the dependency layer cache).
COPY app/ ./app/

# Flush stdout/stderr immediately — important for container log collection
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

# Expose the port uvicorn listens on
EXPOSE 8000

# Use `python -m uvicorn` (module invocation) rather than the uvicorn script
# so Python resolves the interpreter itself — no shebang path issues.
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
