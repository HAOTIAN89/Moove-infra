vllm serve OpenMeditron/Meditron3-8B \
    --tensor-parallel-size 2 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.7 \
    --port 8080 