from elasticsearch import Elasticsearch
import pandas as pd
from tqdm import tqdm

import config

client = Elasticsearch(
    config.ELASTIC_HOST,
    ca_certs=config.CA_CERT,
    api_key=config.ELASTIC_API_KEY
)

eb_index = "hto_eb"

eb_settings = {
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

eb_mappings = {
    "properties": {
        "embedding": {
            "type": "dense_vector",
            "similarity": "cosine"
        },
        "collection": {"type": "constant_keyword", "value": "Encyclopaedia Britannica"},
        "edition_uri": {"type": "keyword"},
        "vol_num": {"type": "integer"},
        "vol_title": {"type": "keyword"},
        "genre": {"type": "keyword"},
        "print_location": {"type": "keyword"},
        "year_published": {"type": "integer"},
        "edition_num": {"type": "integer"},
        "supplements_to": {"type": "integer"},
        "name": {"type": "text",
                 "fields": {
                     "keyword": {
                         "type": "keyword"
                     }
                 }
        },
        "alter_names": {"type": "text"},
        "term_type": {"type": "keyword"},
        "note": {"type": "text"},
        "start_page_num": {"type": "integer"},
        "end_page_num": {"type": "integer"},
        "reference_terms": {
            "type": "nested",
            "properties": {
                "uri": {"type": "keyword"},
                "name": {"type": "text"}
            }
        },
        "sentiment": {
            "type": "nested",
            "properties": {
                "label": {"type": "keyword"},
                "score": {"type": "float"}
            }
        },
        "concept_uri": {"type": "keyword"},
        "description": {"type": "text"},
        "description_uri": {"type": "keyword"},
    }
}


if __name__ == "__main__":
    # Load the dataframe
    eb_kg_hq_dataframe = pd.read_json("ingest_data/eb_hq_dataframe_composite", orient="index")
    eb_kg_hq_dataframe["edition_num"].fillna(0, inplace=True)
    eb_kg_hq_dataframe.rename(columns={"term_name": "name"}, inplace=True)
    eb_kg_hq_dataframe["collection"] = "Encyclopaedia Britannica"
    # Create the index with the defined mapping
    if not client.indices.exists(index=eb_index):
        client.indices.create(index=eb_index, settings=eb_settings, mappings=eb_mappings)

    terms_list = eb_kg_hq_dataframe.to_dict('records')
    total = len(terms_list)
    count = 0
    with tqdm(total=total, desc="Ingestion Progress", unit="step") as pbar:
        for doc in terms_list:
            count += 1
            pbar.update(1)
            client.index(index=eb_index, id=doc["term_uri"], document=doc)