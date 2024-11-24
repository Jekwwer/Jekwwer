# .devcontainer/Dockerfile: Sets up the development container for the project.

# Use the existing devcontainer image as the base
FROM mcr.microsoft.com/devcontainers/python:3.12

# Set environment variable to non-interactive mode for apt-get installations
ENV DEBIAN_FRONTEND=noninteractive

# Define ARGs for the version of each package
ARG HADOLINT_VERSION=v2.12.0

# Set working directory
WORKDIR /workspace

# Copy pyproject.toml to install dependencies
COPY pyproject.toml ./

# Install Hadolint
RUN apt-get update && \
    wget --progress=dot:giga -O /usr/local/bin/hadolint https://github.com/hadolint/hadolint/releases/download/${HADOLINT_VERSION}/hadolint-Linux-x86_64 && \
    chmod +x /usr/local/bin/hadolint && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the PYTHONPATH environment variable
ENV PYTHONPATH=/workspace:$PYTHONPATH

# Upgrade pip and install project dependencies with version constraints from pyproject.toml
RUN pip install --no-cache-dir -e ".[dev,lint,format,mypy,bandit]"
