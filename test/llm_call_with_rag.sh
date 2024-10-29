#!/bin/bash
curl -X 'POST' \
  'http://localhost:7070/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -d '{
  "model": "OpenMeditron/Meditron3-8B",
  "messages": [
        {"role": "user", "content": "Hello, I feel dizzy now after drinking a bottle of beer. What should I do?"}
    ],
  "max_tokens": 3396,
  "stream": true,
  "with_rag": true,
  "group_name": "group1",
  "top_k": 3
}'