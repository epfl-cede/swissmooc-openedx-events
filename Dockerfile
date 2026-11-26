FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace

# Toolchain image only: dependencies are installed here, source is always
# volume-mounted at /workspace at runtime (see the Makefile).
RUN pip install --no-cache-dir \
    "Django>=4.2" \
    "djangorestframework>=3.14" \
    "ruff>=0.6" \
    "mypy>=1.11"

CMD ["bash"]
