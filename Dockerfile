FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV A4I_DATASET=a4i_housing
ENV A4I_LOCATION=US

COPY agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt uvicorn fastapi pydantic

COPY agent/ ./agent/
COPY sql/ ./sql/

EXPOSE 8080

CMD ["python", "-m", "agent.server"]
