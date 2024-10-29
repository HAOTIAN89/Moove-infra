curl -X 'DELETE' \
  'http://127.0.0.1:8001/delete_document/' \
  -H 'Content-Type: application/json' \
  -d '{
  "group_name": "group1",
  "document_name": "Green Tea"
}'