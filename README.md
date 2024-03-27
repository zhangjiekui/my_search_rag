# my_search_rag
# 启动xinference
docker run \
--shm-size=64g \
--name my_xinference -d -p 9997:9997 -e XINFERENCE_MODEL_SRC=modelscope \
-v /home/jqsoft/.xinference:/root/.xinference \
-v /home/jqsoft/.cache/huggingface:/root/.cache/huggingface \
-v /home/jqsoft/.cache/modelscope:/root/.cache/modelscope \
--gpus all xprobe/xinference:revised xinference-local -H 0.0.0.0 --log-level debug
# 运行qwen1.5-chat
CUDA_VISIBLE_DEVICES=0,1,2,3 xinference launch --model-name qwen1.5-chat --size-in-billions 72 --n_gpu 4 --model-format gptq --quantization Int4  --gpu_memory_utilization 0.85 --tensor_parallel_size 4 --log-level debug
