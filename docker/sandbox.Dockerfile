# Goldseam Hardened Sandbox Image
FROM python:3.12-slim

# Prevent python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspace

# Install pytest inside the sandbox
RUN pip install --no-cache-dir pytest>=8.0.0

# Create non-root unprivileged sandbox user
RUN groupadd -g 10001 sandbox && \
    useradd -u 10001 -g sandbox -m -s /sbin/nologin sandbox

# Set up clean sandbox workdir
WORKDIR /workspace
RUN chown -R sandbox:sandbox /workspace

# Switch to unprivileged user
USER 10001:10001

# Default command runs pytest against mounted test suites
CMD ["pytest", "-q", "--tb=short"]
