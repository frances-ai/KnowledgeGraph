from elasticsearch import Elasticsearch
import pandas as pd
from tqdm import tqdm

client = Elasticsearch(
  "https://83a1253d6aac48278867d36eed60b642.us-central1.gcp.cloud.es.io:443",
  api_key="cmtBajU0MEJiRUoteDA3bmtubEE6bHpVYzFlSWNUSXFWcG8tbHFnOUFxQQ=="
)

eb_index = "eb"


if __name__ == "__main__":
    # Load the dataframe
    term_sentiment_dataframe = pd.read_json("eb_topic_dataframe", orient="index")

    topic_dict = {}
    for index, row in term_sentiment_dataframe.iterrows():
        topic_dict[row["term_uri"]] = row["topic_num"]
    total = len(topic_dict)
    count = 0
    with tqdm(total=total, desc="Ingestion Progress", unit="step") as pbar:
        for doc_id, new_value in topic_dict.items():
            response = client.update(
                index=eb_index,
                id=doc_id,
                body={
                    "doc": {
                        "topic_num": new_value
                    }
                }
            )
            pbar.update(1)