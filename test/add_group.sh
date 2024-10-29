#!/bin/bash
curl -X 'POST' \
  'http://localhost:7070/add_group/' \
  -H 'Content-Type: application/json' \
  -d '{
  "group_name": "group2"
}'