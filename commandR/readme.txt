###  aphrodite 支持commandR模型 + openai接口，也有langchain的集成
https://github.com/PygmalionAI/aphrodite-engine
https://python.langchain.com/docs/integrations/llms/aphrodite/

1、docker image下载: docker pull alpindale/aphrodite-engine
2、运行
1）105模型地址 model_id = "/home/jqsoft/.cache/modelscope/hub/AI-ModelScope/c4ai-command-r-v01"
sudo docker run -d -e MODEL_NAME="mistralai/Mistral-7B-Instruct-v0.2" -p 2242:7860 --gpus all --ipc host alpindale/aphrodite-engine

docker run -d \
--shm-size=64g \
-v /home/jqsoft/.xinference:/root/.xinference \
-v /home/jqsoft/.cache/huggingface:/root/.cache/huggingface \
-v /home/jqsoft/.cache/modelscope:/root/.cache/modelscope \
-e MODEL_NAME="/root/.cache/modelscope/hub/AI-ModelScope/c4ai-command-r-v01" \
-e HF_CACHE=/root/.cache/huggingface \
-e HF_HUB_ENABLE_HF_TRANSFER=1 \
-e NUM_GPUS=4 \
-e GPU_MEMORY_UTILIZATION=0.85 \
-p 2242:7860 --gpus all --ipc host alpindale/aphrodite-engine \
