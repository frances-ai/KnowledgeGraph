import hdbscan
import pandas as pd
import umap
from bertopic import BERTopic
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from bertopic.representation import KeyBERTInspired, MaximalMarginalRelevance, PartOfSpeech

from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer('all-mpnet-base-v2')

# Define UMAP model to reduce embeddings dimension
umap_model = umap.UMAP(n_neighbors=15,
                       n_components=10,
                       min_dist=0.0,
                       metric='cosine',
                       low_memory=False,
                       random_state=42)

# Define HDBSCAN model to perform documents clustering
hdbscan_model = hdbscan.HDBSCAN(min_cluster_size=10,
                                min_samples=1,
                                metric='euclidean',
                                cluster_selection_method='eom',
                                prediction_data=True)

# Improving Default Representation
vectorizer_model = CountVectorizer(stop_words="english", min_df=2, ngram_range=(1, 2))

# Additional representations

# KeyBERT
keybert_model = KeyBERTInspired()

# Part-of-Speech
pos_model = PartOfSpeech("en_core_web_sm")

# MMR
mmr_model = MaximalMarginalRelevance(diversity=0.3)

# All representation models
representation_model = {
    "KeyBERT": keybert_model,
    # "OpenAI": openai_model,  # Uncomment if you will use OpenAI
    "MMR": mmr_model,
    "POS": pos_model
}

topic_model = BERTopic(
    # Pipeline models
    embedding_model=embedding_model,
    umap_model=umap_model,
    hdbscan_model=hdbscan_model,
    vectorizer_model=vectorizer_model,
    #representation_model=representation_model,
    # Hyperparameters
    top_n_words=20,
    calculate_probabilities=True,
    verbose=True)


def run_task(inputs):
    eb_kg_df_filename = inputs["dataframe"]["filename"]
    eb_kg_df = pd.read_json(eb_kg_df_filename, orient="index")
    descriptions = [row['summary'] if row['summary'] is not None else row['description'] for index, row in
                    eb_kg_df.iterrows()]

    embeddings = np.array([np.array(x) for x in eb_kg_df['embedding']])
    print("fit transform")
    topics, probs = topic_model.fit_transform(descriptions, embeddings)

    # Custom labels
    custom_topic_labels = {}
    for topic_num in topic_model.get_topics():
        values = topic_model.get_topic(topic_num)
        topic_name = " | ".join([name for name, probs in values[:5]])
        custom_topic_labels[topic_num] = topic_name
    custom_topic_labels[-1] = "Outlier Topic"
    topic_model.set_topic_labels(custom_topic_labels)

    eb_topic_list = []
    print(f"Creating result dataframe.....")
    for index in range(len(eb_kg_df)):
        term_uri = eb_kg_df.loc[index, 'term_uri']
        topic_num = topics[index]
        topic_info = topic_model.get_topic_info(topic_num)
        topic_count = topic_info['Count']
        topic_name = topic_info['CustomName']
        topic_representation = topic_info['Representation']
        eb_topic_list.append([term_uri, topic_num, topic_count, topic_name, topic_representation])

    eb_topic_df = pd.DataFrame(eb_topic_list, columns=["term_uri", "topic_num", "topic_count", "topic_name", "topic_representation"])
    result_df_filename = inputs["results_filenames"]["dataframe"]
    print(f"Saving result dataframe to {result_df_filename}")
    eb_topic_df.to_json(result_df_filename, orient="index")
    result_topic_model_dir = inputs["results_filenames"]["topic_model"]
    print(f"Saving topic model to {result_topic_model_dir}")
    # Serialization
    topic_model.save(result_topic_model_dir, serialization="safetensors", save_ctfidf=True,
                     save_embedding_model=embedding_model)
