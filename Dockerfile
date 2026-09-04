# syntax=docker/dockerfile:1
# Multi-stage reproducible container for ngest biomedical knowledge graph pipeline

FROM condaforge/mambaforge:24.3.0-0 AS base

LABEL maintainer="Hugo Martiniano <hugomartiniano@gmail.com>"
LABEL description="ngest: Automated pipeline for building standardized biomedical Knowledge Graphs"
LABEL org.opencontainers.image.source="https://github.com/hmartiniano/ngest"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    graphviz \
    libxml2-dev \
    libxslt1-dev \
    make \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Conda/Mamba dependencies
COPY env.yml /app/env.yml
RUN mamba env update -n base -f /app/env.yml && \
    mamba clean --all -f -y

# Install testing and linting packages into base env
RUN pip install --no-cache-dir pytest flake8

# Copy repository source code
COPY config/ /app/config/
COPY workflow/ /app/workflow/
COPY docs/ /app/docs/
COPY tests/ /app/tests/
COPY Makefile /app/Makefile
COPY README.md /app/README.md
COPY TODO.md /app/TODO.md

# Pre-create standard data directories
RUN mkdir -p /app/data/raw \
             /app/data/processed/finals \
             /app/data/processed/intermediary \
             /app/data/processed/mappings

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PAGER=cat \
    SNAKEMAKE_OUTPUT_CACHE=/app/.snakemake/cache

# Default workdir is the workflow directory for Snakemake execution
WORKDIR /app/workflow

# Default entrypoint runs snakemake
ENTRYPOINT ["snakemake"]
CMD ["-c", "8", "all"]
