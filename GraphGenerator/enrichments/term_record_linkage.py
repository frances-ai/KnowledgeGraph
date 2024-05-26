import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm


def get_similar_terms_grouped_by_years_sorted_by_score(df):
    """
    This function will calculate the cosine similarities based on the embeddings in the dataframe, sort the scores and group the result by the year when the record is published.
    :param df: input dataframe, which contain the embedding for each term, and year published information
    :return: {
        df_index: {
            1771: [
                {
                    "index": <dataframe index of the similar term>,
                    "score": <cosine similarity score>
                }, ...
            ],
            1815: [
            ],....
        },
        ......
    }
    """
    embeddings = df["embedding"].values.tolist()
    indices = df.index
    similarities=cosine_similarity(embeddings, embeddings)
    similarities_sorted = similarities.argsort()
    result = {}
    for i in range(len(similarities_sorted)):
        for j in similarities_sorted[i][::-1]:
            year = df.loc[indices[j], "year_published"]
            sim_info = {
                    "index": indices[j],
                    "score": similarities[i][j]
                }
            if indices[i] not in result:
                result[indices[i]] = {}
                result[indices[i]][year] = [sim_info]
            else:
                if year in result[indices[i]]:
                    result[indices[i]][year].append(sim_info)
                else:
                    result[indices[i]][year] = [sim_info]

    return result


def group_terms_to_concept(df):
    """
    This function will link terms and group term into concepts, each concept have uri, which can be used in
    knowledge graph.
    :param df: df: input dataframe, which contain the embedding for each term, term_uri, and year published information
    :return: df: original dataframe with extra column "concept_uri".
    """
    # Get all distinct term names
    term_names = df["term_name"].unique()
    # initialise concept_uri
    df["concept_uri"] = None

    for term_name in tqdm(term_names):
        # all terms with term_name
        terms_df = df[df["term_name"] == term_name]
        years = terms_df["year_published"].unique().tolist()
        years.sort()
        #print(years)
        concept_count = 0
        similarities = get_similar_terms_grouped_by_years_sorted_by_score(terms_df)
        # generate id for the concept
        concept_id = str(terms_df["term_uri"].values.tolist()[0]).split("/")[-1].split("_")[-2]
        for year_index in range(len(years)):
            year = years[year_index]
            #print(f"processing terms {term_name} in {year} ")
            # all terms with term_name and the year
            terms_year_df = terms_df[terms_df["year_published"] == year]
            for index, row in terms_year_df.iterrows():
                #print(f"linking term with index {index} with other terms across years")
                # print(f"description of the term: {row['description']}")
                concept_uri = df.loc[index, "concept_uri"]
                if concept_uri is None:
                    concept_count += 1
                    concept_uri = "https://w3id.org/hto/Concept/" + str(concept_id) + "_" + str(concept_count)
                    df.loc[index, "concept_uri"] = concept_uri

                # find most similar terms in each following years
                similarity_threshold = 0.7
                for f_year_index in years[year_index + 1:]:
                    most_similar_term = similarities[index][f_year_index][0]
                    score = most_similar_term["score"]
                    similar_term_index = most_similar_term["index"]
                    # skip if there is concept uri linked to it already, or the score is below the threshold, or there is another term in this year is more similar the most_similar_term
                    if score > similarity_threshold:
                        if df.loc[similar_term_index, "concept_uri"] is None:
                            if similarities[similar_term_index][year][0]["index"] == index:
                                df.loc[similar_term_index, "concept_uri"] = concept_uri
                                #print(f"year: {f_year_index}, term {most_similar_term} is linked")
                            else:
                                pass
                                #print(f"year: {f_year_index}, term {most_similar_term} is skipped, because term {similarities[similar_term_index][year][0]['index']} is more similar to the most_similar_term")
                        else:
                            if df.loc[similar_term_index, "concept_uri"] == concept_uri:
                                pass
                                #print("same concept uri")
                                #print(f"year: {f_year_index}, term {most_similar_term} is skipped, because it is linked already")
                            else:
                                # This is the solution when the link can't be made directly. e.g. escort: 1797-1815-1823， 1810-1815-2823,
                                concept_uri = df.loc[similar_term_index, "concept_uri"]
                                df.loc[index, "concept_uri"] = concept_uri
                                #print(f"replace the concept uri to the one same with {most_similar_term}")
                    else:
                        pass
                        #print(f"year: {f_year_index}, term {most_similar_term} is skipped, because it is not quite similar")

    return df


def run_task(inputs):
    print("Loading dataframe.....")
    eb_kg_df_filename = inputs["dataframe"]["filename"]
    eb_kg_df = pd.read_json(eb_kg_df_filename, orient="index")
    print("Grouping terms into concepts.....")
    df = group_terms_to_concept(eb_kg_df)
    result_df_filename = inputs["results_filenames"]["dataframe"]
    print(f"Saving dataframe to file: {result_df_filename}")
    df.to_json(result_df_filename, orient="index")

