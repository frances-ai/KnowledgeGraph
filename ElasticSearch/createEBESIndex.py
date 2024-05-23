from elasticsearch import Elasticsearch
import pandas as pd
from tqdm import tqdm

client = Elasticsearch(
  "https://83a1253d6aac48278867d36eed60b642.us-central1.gcp.cloud.es.io:443",
  api_key="cmtBajU0MEJiRUoteDA3bmtubEE6bHpVYzFlSWNUSXFWcG8tbHFnOUFxQQ=="
)

eb_index = "eb"

eb_mapping = {
    "mappings": {
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
            "concept_uri": {"type": "keyword"},
            "similar_terms": {
                "type": "nested",
                "properties": {
                    "uri": {"type": "keyword"},
                    "name": {"type": "keyword"},
                    "year": {"type": "integer"},
                    "score": {"type": "double"}
                }
            },
            "description": {"type": "text"},
            "description_uri": {"type": "keyword"},
        }
    }
}

if __name__ == "__main__":
    # Load the dataframe
    eb_kg_hq_dataframe = pd.read_json("eb_kg_hq_normalised_embeddings_concepts_dataframe", orient="index")
    eb_kg_hq_dataframe["edition_num"].fillna(0, inplace=True)
    eb_kg_hq_dataframe.rename(columns={"term_name": "name"}, inplace=True)
    eb_kg_hq_dataframe["collection"] = "Encyclopaedia Britannica"
    # Create the index with the defined mapping
    if not client.indices.exists(index=eb_index):
        client.indices.create(index=eb_index, body=eb_mapping)

    terms_list = eb_kg_hq_dataframe.to_dict('records')
    total = len(terms_list)
    count = 0
    with tqdm(total=total, desc="Ingestion Progress", unit="step") as pbar:
        for doc in terms_list:
            count += 1
            pbar.update(1)
            client.index(index=eb_index, id=doc["term_uri"], document=doc)
