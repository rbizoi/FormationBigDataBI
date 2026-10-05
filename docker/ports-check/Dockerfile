FROM docker:28-cli
RUN apk add --no-cache python3
WORKDIR /project
COPY check_ports.py /app/check_ports.py
ENTRYPOINT ["python3", "/app/check_ports.py"]
