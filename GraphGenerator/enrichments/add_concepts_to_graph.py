import pandas as pd
from rdflib import URIRef, RDF, Literal, XSD
from tqdm import tqdm

# load the graph
from rdflib import Graph, Namespace, RDF

# Load the existing graph
graph = Graph()
graph.parse(location="../../hto_v1_infer.ttl", format="turtle")

hto = Namespace("https://w3id.org/hto#")

def record_links(kg_df_with_concept_uris):
    concept_uris = kg_df_with_concept_uris["concept_uri"].unique()
    for concept_uri in tqdm(concept_uris):
        if concept_uri:
            concept_records_df = kg_df_with_concept_uris[kg_df_with_concept_uris["concept_uri"] == concept_uri]
            concept_uriref = URIRef(concept_uri)
            graph.add((concept_uriref, RDF.type, hto.Concept))
            for index, row in concept_records_df.iterrows():
                record_uri_ref = URIRef(row["term_uri"])
                graph.add((concept_uriref, hto.hadConceptRecord, record_uri_ref))

        else:
            print("None")

def external_link(concept_item_df, type_uri):
    for index, row in concept_item_df.iterrows():
        concept_uri = row["concept_uri"]
        item_uri = row["item_uri"]
        #print(concept_uri, item_uri)
        concept_uriref = URIRef(concept_uri)
        item_uriref = URIRef(item_uri)
        graph.add((item_uriref, RDF.type, hto.ExternalRecord))
        graph.add((item_uriref, RDF.type, hto.InformationResource))
        graph.add((item_uriref, hto.hasResourceType, type_uri))
        graph.add((concept_uriref, hto.hadConceptRecord, item_uriref))


def run_task(inputs):
    # add record links
    print("Loading the source dataframe with concept uris .....")
    df_with_concept_uris_filename = inputs["record_dataframe"]["filename"]
    df_with_concept_uris = pd.read_json(df_with_concept_uris_filename, orient="index")
    print("Adding links from records to concepts .....")
    record_links(df_with_concept_uris)
    #graph.serialize(format="turtle", destination="gaz_extra_concepts_records_link.ttl")

    # add wikidata links
    print("Loading the wikidata items dataframe .....")
    concept_wiki_df_filename = inputs["wiki_dataframe"]["filename"]
    concept_wiki_df = pd.read_json(concept_wiki_df_filename, orient="index")
    print("Adding links from wikidata items to concepts .....")
    external_link(concept_wiki_df, hto.Wikidata_Item)
    #graph.serialize(format="turtle", destination="gaz_extra_concepts_wikidata_link.ttl")

    # add dbpedia links
    print("Loading the dbpedia items dataframe .....")
    concept_dbpedia_df_filename = inputs["dbpedia_dataframe"]["filename"]
    concept_dbpedia_df = pd.read_json(concept_dbpedia_df_filename, orient="index")
    print("Adding links from dbpedia items to concepts .....")
    external_link(concept_dbpedia_df, hto.DBpedia_Item)

    result_df_filename = inputs["results_filenames"]["dataframe"]
    result_graph_filepath = "results/" + result_df_filename
    print(f"Saving the result graph to {result_graph_filepath} .....")
    graph.serialize(format="turtle", destination=result_graph_filepath)
    print("Done")
