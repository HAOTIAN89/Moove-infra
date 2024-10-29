curl -X 'DELETE' \
  'http://localhost:7070/delete_group/' \
  -H 'Content-Type: application/json' \
  -d '{
  "group_name": "group2"
}'