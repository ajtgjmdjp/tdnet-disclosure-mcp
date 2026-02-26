FROM python:3.12-slim

RUN pip install --no-cache-dir tdnet-disclosure-mcp

ENTRYPOINT ["tdnet-disclosure-mcp"]
CMD ["serve"]
