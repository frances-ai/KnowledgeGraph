from elasticsearch import Elasticsearch

HOST = "https://elastic.frances-ai.com:9200/"
CA_CERT_PATH = "<path_to_your_ca_cert>"
ELASTIC_API_KEY = "<your_elastic_api_key>"


client = Elasticsearch(
    HOST,
    ca_certs=CA_CERT_PATH,
    api_key=ELASTIC_API_KEY
)


def search_match_all(top_n=10, index_names="hto_*"):
    """
    This function retrieve the top n results from ElasticSearch match_all query.
    :param top_n: the first n results from the match_all query, by default 10.
    :param index_names: Comma-separated list of data streams, indices, and aliases to search.
    Supports wildcards (*). By default, it refers to all indices with name starts `hto_`.
    :return: a list with the top n results from the match_all query
    """
    # construct elastic search query body
    body = {
        "query": {
            "match_all": {}
        },
        "from": 0,
        "size": top_n
    }
    response = client.search(index=index_names, body=body)
    hits = response['hits']['hits']
    return hits

if __name__ == "__main__":
    search_result = search_match_all()
    print(search_result)