from elasticsearch import Elasticsearch
import pandas as pd
from tqdm import tqdm

import config

client = Elasticsearch(
    config.ELASTIC_HOST,
    ca_certs=config.CA_CERT,
    api_key=config.ELASTIC_API_KEY
)

index = "hto_broadsides"

settings = {
    "analysis": {
            "analyzer": {
                "default": {
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "kstem",
                        "stop"
                    ]
                },
                "default_search": {
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "kstem",
                        "stop"
                        # synonym_graph
                    ]
                }
            }
        }
}

mappings = {
    "properties": {
        "collection": {"type": "constant_keyword", "value": "Broadsides printed in Scotland"},
        "series_uri": {"type": "keyword"},
        "vol_num": {"type": "integer"},
        "vol_title": {"type": "keyword"},
        "genre": {"type": "keyword"},
        "print_location": {"type": "keyword", "null_value": "Unknown" },
        "year_published": {"type": "integer", "null_value": -1},
        "series_num": {"type": "integer"},
        "name": {"type": "text",
                 "fields": {
                     "keyword": {
                         "type": "keyword"
                     }
                 }
                 },
        "page_num": {"type": "integer"},
        "description": {"type": "text"},
        "description_uri": {"type": "keyword"},
    }
}


if __name__ == "__main__":
    # Load the dataframe
    broadsides_dataframe = pd.read_json("ingest_data/broadsides_kg_hq_dataframe", orient="index")
    broadsides_dataframe["year_published"] = broadsides_dataframe["year_published"].fillna(-1)
    broadsides_dataframe["collection"] = "Broadsides printed in Scotland"
    # Create the index with the defined mapping
    if not client.indices.exists(index=index):
        client.indices.create(index=index, settings=settings, mappings=mappings)

    broadsides_list = broadsides_dataframe.to_dict('records')
    total = len(broadsides_list)
    count = 0
    with tqdm(total=total, desc="Ingestion Progress", unit="step") as pbar:
        for doc in broadsides_list:
            count += 1
            pbar.update(1)
            client.index(index=index, id=doc["record_uri"], document=doc)
