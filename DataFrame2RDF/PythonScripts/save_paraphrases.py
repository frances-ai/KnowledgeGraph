import pandas as pd
from sentence_transformers import SentenceTransformer, util
import pickle

model_name = 'all-mpnet-base-v2'

model = SentenceTransformer(model_name)


def paraphrases_mining(descriptions):
    return util.paraphrase_mining(model, descriptions, corpus_chunk_size=len(descriptions), top_k=20,
                                  show_progress_bar=True)


if __name__ == "__main__":
    eb_kg_df = pd.read_json("../../eb_kg_hq_dataframe", orient="index")
    descriptions = [row['summary'] if row['summary'] is not None else row['description'] for index, row in eb_kg_df.iterrows()]

    paraphrases = paraphrases_mining(descriptions)

    paraphrases_file = open("../../paraphrases", 'wb')
    pickle.dump(paraphrases, paraphrases_file)