import pandas as pd
from transformers import pipeline
from tqdm.auto import tqdm

sentiment_analysis = pipeline("sentiment-analysis",model="siebert/sentiment-roberta-large-english")


def get_sentiment_result(description):
    try:
        return sentiment_analysis(description, truncation=True)[0]
    except Exception as e:
        print(e)
        return {'label': 'ERROR', 'score': 0.0}


if __name__ == "__main__":
    eb_kg_hq_dataframe = pd.read_json("../eb_kg_hq_dataframe", orient="index")
    eb_kg_hq_dataframe = eb_kg_hq_dataframe

    tqdm.pandas(desc="Processing sentiment analysis!")
    eb_kg_hq_dataframe["sentiment"] = eb_kg_hq_dataframe['description'].progress_apply(
        lambda description: get_sentiment_result(description))

    term_sentiment_dataframe = eb_kg_hq_dataframe[['term_uri', 'sentiment']]
    result_file = "term_sentiment_dataframe"
    print(f"Saving the result to file: {result_file}")
    term_sentiment_dataframe.to_json(result_file, orient="index")