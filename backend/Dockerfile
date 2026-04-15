FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace/backend

COPY requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
