import pickle

import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
import sys
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

model = SentenceTransformer('all-mpnet-base-v2')
model._first_module().max_seq_length = 509


def invert_name(name: str) -> str:
    """
    Inverts a name from the format 'Last, Prefix' to 'Prefix Last'.

    Parameters:
    name (str): The name to be inverted.

    Returns:
    str: The inverted name.
    """
    # Split the name by ', ' to handle the inversion
    parts = name.split(', ')
    if len(parts) == 2:
        # Invert the order and join without a comma for cases like "Andrews, St"
        inverted_name = f"{parts[1]} {parts[0]}"
    else:
        # Return the original name if it doesn't match the expected pattern
        inverted_name = name

    return inverted_name


# Initialise a sparqlwrapper for dbpedia
user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
dbpedia_endpoint_url = "https://dbpedia.org/sparql/"
dbpedia_sparql = SPARQLWrapper(endpoint=dbpedia_endpoint_url, agent=user_agent)


def get_dbpedia_item_by_name(item_name):
    # Inverts a name from the format 'Last, Prefix' to 'Prefix Last'.
    item_name = invert_name(item_name)
    items = []
    item_valid_names = [item_name.title(), item_name.lower()]
    for item_valid_name in item_valid_names:
        wd_term_search_query = """
            SELECT * WHERE {
                ?item rdfs:label "%s"@en.
                ?item dbo:abstract ?abstract.
                FILTER (lang(?abstract) = "en")
            }
        """ % item_valid_name
        dbpedia_sparql.setQuery(wd_term_search_query)
        dbpedia_sparql.setReturnFormat(JSON)
        dbpedia_term_search_results = dbpedia_sparql.query().convert()
        for result in dbpedia_term_search_results["results"]["bindings"]:
            if "abstract" in result:
                items.append({
                    "uri": result['item']['value'],
                    "description": result['abstract']['value']
                })
    return items


def get_most_similar_item(query_embedding, dbpedia_items):
    item_embeddings = [item["embedding"] for item in dbpedia_items]
    similarities = cosine_similarity([query_embedding], item_embeddings)
    #print(similarities)
    # Find the index of the most similar item
    most_similar_index = np.argmax(similarities)
    score = similarities[0][most_similar_index]
    #print(score)
    return score, dbpedia_items[most_similar_index]


def link_dbpedia_with_concept(df):
    concept_uris = df["concept_uri"].unique()
    all_searched_dbpedia_items = {}
    concept_dbpedia_item_list = []
    exception_concept_uris = []
    for concept_uri in tqdm(concept_uris):
        terms_df = df[df["concept_uri"] == concept_uri]
        terms_df = terms_df.sort_values(by="year_published", ascending=False)
        # get the latest (the largest year) term info
        latest_term_df = terms_df.iloc[0]
        term_name = latest_term_df["term_name"]
        embedding = latest_term_df["embedding"]
        #print(term_name)
        #print(latest_term_df["description"])
        # get dbpedia items, and their embeddings
        dbpedia_items = []
        if term_name in all_searched_dbpedia_items:
            dbpedia_items = all_searched_dbpedia_items[term_name]
        else:
            try:
                dbpedia_items = get_dbpedia_item_by_name(term_name)
                # get embeddings for each item
                items_descriptions = [item["description"] for item in dbpedia_items]
                #print(items_descriptions)
                item_embeddings = model.encode(items_descriptions).tolist()
                # Add each embedding to its corresponding item
                for dbpedia_item, dbpedia_embedding in zip(dbpedia_items, item_embeddings):
                    dbpedia_item['embedding'] = dbpedia_embedding
                all_searched_dbpedia_items[term_name] = dbpedia_items
            except:
                exception_concept_uris.append(concept_uri)
        if len(dbpedia_items) > 0:
            score, most_similar_dbpedia_item = get_most_similar_item(embedding, dbpedia_items)
            #print(most_similar_wiki_item["description"])
            if score > 0:
                concept_dbpedia_item_list.append({
                    "concept_uri": concept_uri,
                    "item_uri":  most_similar_dbpedia_item["uri"],
                    "item_description": most_similar_dbpedia_item["description"],
                    "similar_score": score,
                    "embedding": most_similar_dbpedia_item["embedding"]
                })

    return exception_concept_uris, concept_dbpedia_item_list


def run_task(inputs):
    print("Reading the source dataframe .....")
    eb_kg_df_filename = inputs["dataframe"]["filename"]
    eb_kg_df = pd.read_json(eb_kg_df_filename, orient="index")
    print("Linking dbpedia items.......")
    exception_concept_uris, concept_dbpedia_item_list = link_dbpedia_with_concept(eb_kg_df)
    concept_dbpedia_item_df = pd.DataFrame(concept_dbpedia_item_list)
    result_df_filename = inputs["results_filenames"]["dataframe"]
    print(f"Saving the result to file: {result_df_filename}")
    concept_dbpedia_item_df.to_json(result_df_filename, orient="index")
    exception_concept_uris_file = "dbpedia_exception_concept_uris.pkl"
    print(f"Saving the exception concept uris to file: {exception_concept_uris_file}")
    with open(exception_concept_uris_file, 'wb') as f:
        pickle.dump(exception_concept_uris, f)



