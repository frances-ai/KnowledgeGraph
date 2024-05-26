from elasticsearch import Elasticsearch
import pandas as pd
from tqdm import tqdm

import config

client = Elasticsearch(
  config.ELASTIC_HOST,
  api_key=config.ELASTIC_API_KEY
)

eb_index = "eb"


if __name__ == "__main__":
    # Load the dataframe
    term_sentiment_dataframe = pd.read_json("KnowledgeEnrichment/term_sentiment_dataframe", orient="index")

    sentiment_dict = {}
    for index, row in term_sentiment_dataframe.iterrows():
        sentiment_dict[row["term_uri"]] = row["sentiment"]
    total = len(sentiment_dict)
    count = 0
    with tqdm(total=total, desc="Ingestion Progress", unit="step") as pbar:
        for doc_id, new_value in sentiment_dict.items():
            response = client.update(
                index=eb_index,
                id=doc_id,
                body={
                    "doc": {
                        "sentiment": new_value
                    }
                }
            )
            pbar.update(1)