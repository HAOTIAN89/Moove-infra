#!/bin/bash
curl -X 'GET' \
  'http://localhost:7070/get_groups/' \
  -H 'Content-Type: application/json' \
  -d '{
  "group_name": "group1"
}'