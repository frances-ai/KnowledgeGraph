from elasticsearch import Elasticsearch
import pandas as pd
from tqdm import tqdm

import config

client = Elasticsearch(
    config.ELASTIC_HOST,
    ca_certs=config.CA_CERT,
    api_key=config.ELASTIC_API_KEY
)

wikidata_index = "wikidata_items"

wikidata_mapping = {
    "mappings": {
        "properties": {
            "embedding": {
                "type": "dense_vector",
                "similarity": "cosine"
            },
            "item_uri": {"type": "keyword"},
            "concept_uri": {"type": "keyword"},
            "description": {"type": "text"}
        }
    }
}


if __name__ == "__main__":
    # Load the dataframe
    concept_wikidata_df = pd.read_json("ingest_data/concept_wikidata_dataframe", orient="index")
    concept_wikidata_df.drop(columns=["max_score"], inplace=True)

    # Create the index with the defined mapping
    if not client.indices.exists(index=wikidata_index):
        client.indices.create(index=wikidata_index, body=wikidata_mapping)

    wikidata_items_list = concept_wikidata_df.to_dict('records')
    total = len(wikidata_items_list)
    count = 0
    with tqdm(total=total, desc="Ingestion Progress", unit="step") as pbar:
        for doc in wikidata_items_list:
            count += 1
            pbar.update(1)
            client.index(index=wikidata_index, id=doc["item_uri"], document=doc)
