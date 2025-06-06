from elasticsearch import Elasticsearch
import pandas as pd
from tqdm import tqdm

import config

client = Elasticsearch(
    config.ELASTIC_HOST,
    ca_certs=config.CA_CERT,
    api_key=config.ELASTIC_API_KEY
)

index = "hto_gazetteers"

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
        "collection": {"type": "constant_keyword", "value": "Gazetteers of Scotland"},
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
        "alter_names": {"type": "text"},
        "term_type": {"type": "keyword"},
        "page_num": {"type": "integer"},
        "description": {"type": "text"},
        "description_uri": {"type": "keyword"},
    }
}


if __name__ == "__main__":
    # Load the dataframe
    gazetteers_dataframe = pd.read_json("ingest_data/gazetteers_kg_nls_dataframe", orient="index")
    gazetteers_dataframe["year_published"].fillna(-1, inplace=True)
    gazetteers_dataframe["name"] = gazetteers_dataframe["vol_title"]
    # Create the index with the defined mapping
    if not client.indices.exists(index=index):
        client.indices.create(index=index, mappings=mappings, settings=settings)

    page_list = gazetteers_dataframe.to_dict('records')
    total = len(page_list)
    count = 0
    with tqdm(total=total, desc="Ingestion Progress", unit="step") as pbar:
        for doc in page_list:
            count += 1
            pbar.update(1)
            client.index(index=index, id=doc["page_uri"], document=doc)
