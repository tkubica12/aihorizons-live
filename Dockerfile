FROM python:3.13-slim

WORKDIR /app
RUN python -m pip install --no-cache-dir --index-url https://packagefeedproxy.microsoft.io/pypi/simple/ "uv==0.12.9"
COPY pyproject.toml uv.lock ./
COPY src ./src
COPY database ./database
COPY sample-data/catalog.json ./sample-data/catalog.json
COPY sample-data/order-history.json ./sample-data/order-history.json
RUN uv sync --frozen --no-dev --no-editable

ENV PATH="/app/.venv/bin:$PATH" PIZZA_DATA_ROOT="/app"
EXPOSE 8000
CMD ["uvicorn", "pizza_mcp.server:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
