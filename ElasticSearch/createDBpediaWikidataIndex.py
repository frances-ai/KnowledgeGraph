from elasticsearch import Elasticsearch
import pandas as pd
from tqdm import tqdm
import config

client = Elasticsearch(
  config.ELASTIC_HOST,
  api_key=config.ELASTIC_API_KEY
)

index = "dbpedia_items"

mapping = {
    "mappings": {
        "properties": {
            "embedding": {
                "type": "dense_vector",
                "similarity": "cosine"
            },
            "item_uri": {"type": "keyword"},
            "concept_uri": {"type": "keyword"},
            "item_description": {"type": "text"}
        }
    }
}


def group_by_item(concept_dataframe):
    grouped = concept_dataframe.groupby('item_uri')
    df = pd.DataFrame({
        'item_uri': [name for name, _ in grouped],
        'item_description': [group['item_description'].iloc[0] for name, group in grouped],
        'embedding': [group['embedding'].iloc[0] for name, group in grouped],  # Directly taking the first list
        'concept_uri': [group['concept_uri'].tolist() for name, group in grouped]
    })
    return df


if __name__ == "__main__":
    # Load the dataframe
    concept_df = pd.read_json("concept_dbpedia_dataframe", orient="index")

    # Create the index with the defined mapping
    if not client.indices.exists(index=index):
        client.indices.create(index=index, body=mapping)

    # group by items
    items_df = group_by_item(concept_df)
    items_list = items_df.to_dict('records')
    total = len(items_list)
    count = 0
    with tqdm(total=total, desc="Ingestion Progress", unit="step") as pbar:
        for doc in items_list:
            count += 1
            pbar.update(1)
            client.index(index=index, id=doc["item_uri"], document=doc)
