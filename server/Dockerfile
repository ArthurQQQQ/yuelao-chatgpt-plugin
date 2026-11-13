FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && useradd --system --uid 10001 yuelao
COPY yuelao_mvp/ yuelao_mvp/
COPY cases.sqlite3 .
ENV YUELAO_CASE_DB=/app/cases.sqlite3 PYTHONDONTWRITEBYTECODE=1
USER 10001
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "yuelao_mvp.cloud_mcp:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
