FROM python:3.12-slim as builder
RUN pip install uv
COPY . /app
WORKDIR /app
RUN uv sync --frozen --no-dev

FROM python:3.12-slim
RUN pip install uv
COPY --from=builder /app /app
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "src.main"]

