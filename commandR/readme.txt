###  aphrodite 支持commandR模型 + openai接口，也有langchain的集成
https://github.com/PygmalionAI/aphrodite-engine
https://python.langchain.com/docs/integrations/llms/aphrodite/

1、docker image下载: docker pull alpindale/aphrodite-engine
2、运行
1）105模型地址 model_id = "/home/jqsoft/.cache/modelscope/hub/AI-ModelScope/c4ai-command-r-v01"
官方运行示例：sudo docker run -d -e MODEL_NAME="mistralai/Mistral-7B-Instruct-v0.2" -p 2242:7860 --gpus all --ipc host alpindale/aphrodite-engine

sudo docker run -it --user root \
--shm-size=64g \
-v /home/jqsoft/.cache/modelscope/hub/AI-ModelScope/c4ai-command-r-v01:/tmp/hub/c4ai-command-r-v01 --privileged=true \
-e MODEL_NAME=/tmp/hub/c4ai-command-r-v01 \
-e HF_HUB_ENABLE_HF_TRANSFER=1 \
-e NUM_GPUS=4 \
-e GPU_MEMORY_UTILIZATION=0.95 \
-e CONTEXT_LENGTH=4000 \
-p 2242:7860 --gpus all --ipc host alpindale/aphrodite-engine \
/bin/bash

就可以访问:http://10.1.150.105:2242/docs
