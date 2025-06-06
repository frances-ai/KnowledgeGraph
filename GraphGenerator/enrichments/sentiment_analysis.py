import pandas as pd
from transformers import pipeline
from tqdm.auto import tqdm


def get_sentiment_result(description, sentiment_analysis):
    try:
        return sentiment_analysis(description, truncation=True)[0]
    except Exception as e:
        print(e)
        return {'label': 'ERROR', 'score': 0.0}


def run_task(inputs):
    sentiment_analysis = pipeline("sentiment-analysis", model="siebert/sentiment-roberta-large-english")
    eb_kg_df_filename = inputs["dataframe"]["filename"]
    eb_kg_df = pd.read_json(eb_kg_df_filename, orient="index")

    tqdm.pandas(desc="Processing sentiment analysis!")
    eb_kg_df["sentiment"] = eb_kg_df['description'].progress_apply(
        lambda description: get_sentiment_result(description, sentiment_analysis))

    term_sentiment_dataframe = eb_kg_df[['term_uri', 'sentiment']]
    result_df_filename = inputs["results_filenames"]["dataframe"]
    print(f"Saving the result to file: {result_df_filename}")
    term_sentiment_dataframe.to_json(result_df_filename, orient="index")