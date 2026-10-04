FROM python:3.12.14-slim-bookworm
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && useradd --create-home --uid 10001 --user-group loader
COPY *.py /app/
USER loader
ENTRYPOINT ["python", "/app/load_meteo.py"]
