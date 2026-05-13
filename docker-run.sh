#!/bin/bash
# Start Open WebUI (NeuronAI) Docker container
docker run -d \
  -v open-webui:/app/backend/data \
  -p 3000:8080 \
  -e OLLAMA_BASE_URL=http://172.17.0.1:11434 \
  -e BYPASS_MODEL_ACCESS_CONTROL=true \
  -e DEFAULT_MODELS=llama-3.3-70b-versatile \
  -e WEBUI_NAME=NeuronAI \
  --name open-webui \
  --restart unless-stopped \
  forgeai-webui:latest
