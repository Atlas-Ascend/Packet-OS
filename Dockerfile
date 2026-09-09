FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir .
ENV PORT=8080
EXPOSE 8080
CMD ["python", "-m", "packet_os.httpd"]
