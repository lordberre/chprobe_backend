curl -X POST "http://templabz:rofusrofus@192.168.0.200:8080/api/elasticsearch/_doc/1" -H 'Content-Type: application/json' -d'
{                     
    "user" : "kimchy",
    "post_date" : "2018-10-13T23:45:12",
    "message" : "trying out Elasticsearch"
}
'
# Query for "Location" field to populate an already configured form
curl -X GET "localhost:9200/chprobe_mgmt-*/_search"?pretty -H 'Content-Type: application/json' -d '{"_source": "location","query": { "match_all": {}}}'

