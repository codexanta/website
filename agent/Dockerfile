# Hugging Face Spaces (Docker SDK) - Space must listen on port 7860
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    AGENT_WORKSPACE=/home/user/workspace

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /home/user/app
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

EXPOSE 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
