from elasticsearch import Elasticsearch
import pandas as pd
from tqdm import tqdm

import config

client = Elasticsearch(
  config.ELASTIC_HOST,
  api_key=config.ELASTIC_API_KEY
)

index = "topics"

mapping = {
    "mappings": {
        "properties": {
            "number": {"type": "integer"},
            "item_count": {"type": "integer"},
            "name": {"type": "text"},
            "representation": {"type": "text"}
        }
    }
}


def group_by_item(topic_dataframe):
    grouped = topic_dataframe.groupby('topic_num')
    df = pd.DataFrame({
        'number': [name for name, _ in grouped],
        'item_count': [group['topic_count'].iloc[0] for name, group in grouped],
        'name': [group['topic_name'].iloc[0] for name, group in grouped],  # Directly taking the first list
        'representation': [group['topic_representation'].iloc[0] for name, group in grouped]
    })
    return df


if __name__ == "__main__":
    # Load the dataframe
    topic_df = pd.read_json("eb_topic_dataframe", orient="index")

    # Create the index with the defined mapping
    if not client.indices.exists(index=index):
        client.indices.create(index=index, body=mapping)

    # group by items
    items_df = group_by_item(topic_df)
    items_list = items_df.to_dict('records')
    total = len(items_list)
    count = 0
    with tqdm(total=total, desc="Ingestion Progress", unit="step") as pbar:
        for doc in items_list:
            count += 1
            pbar.update(1)
            client.index(index=index, id=doc["number"], document=doc)