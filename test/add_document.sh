curl -X 'POST' \
  'http://localhost:7070/add_document/' \
  -H 'Content-Type: application/json' \
  -d '{
  "group_name": "group1",
  "chunk_size": 50,
  "document_name": "Green Tea",
  "document": "Green tea has many health benefits such as improved heart health and cognitive function. Film is a great medium of art and expression: on top of providing entertainment, movies can, within their content, also reflect societal characteristics of the era they were produced in. It is well-known that Japanese animation enjoys a lot of acclaim all over the world: many famous animation directors are from Japan, such as Miyazaki Hayao, Kon Satos, Otomo Katsuhiro, Oshii Mamoru, and Shinkai Makoto, among others. Each of these directors has themes of predilection they like to explore, as well as a unique art direction. These Miyazaki Hayao (born 1941) is a long-standing legend in the Japanese animation industry: his works tend to focus on rural worlds, and often feature main characters embarked on journeys of growth through community inside these worlds. Shinkai Makoto (born 1973) is a younger director, who has garnered international success in the past decade. A recurrent theme in his movies is the loneliness and confusion of young people living in Japanese cities"
}'