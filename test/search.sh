curl -X 'POST' \
  'http://localhost:7070/search/' \
  -H 'Content-Type: application/json' \
  -d '{
  "group_name": "group1",
  "query": "What are the health benefits of tea?",
  "top_k": 3
}'