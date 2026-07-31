FROM python:3.11-slim

WORKDIR /app

# Install the official DataHub MCP Server package from PyPI
RUN pip install --no-cache-dir mcp-server-datahub

ENV DATAHUB_GMS_URL=http://datahub-gms:8080

# Launch the DataHub MCP server
CMD ["python", "-m", "mcp_server_datahub"]