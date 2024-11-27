import pandas as pd
from rdflib import URIRef, RDF, Literal, XSD
from tqdm import tqdm

# load the graph
from rdflib import Graph, Namespace, RDF

# Load the existing graph
graph = Graph()
graph.parse(location="../hto.ttl", format="turtle")

hto = Namespace("https://w3id.org/hto#")

def term_links(eb_kg_df_with_concept_uris):
    concept_uris = eb_kg_df_with_concept_uris["concept_uri"].unique()
    for concept_uri in tqdm(concept_uris):
        if concept_uri:
            concept_terms_df = eb_kg_df_with_concept_uris[eb_kg_df_with_concept_uris["concept_uri"] == concept_uri]
            concept_uriref = URIRef(concept_uri)
            graph.add((concept_uriref, RDF.type, hto.Concept))
            for index, row in concept_terms_df.iterrows():
                term_uri_ref = URIRef(row["term_uri"])
                graph.add((concept_uriref, hto.hadConceptRecord, term_uri_ref))

        else:
            print("None")

def external_link(concept_item_df):
    for index, row in concept_item_df.iterrows():
        concept_uri = row["concept_uri"]
        item_uri = row["item_uri"]
        print(concept_uri, item_uri)
        concept_uriref = URIRef(concept_uri)
        item_uriref = URIRef(item_uri)
        graph.add((item_uriref, RDF.type, hto.ExternalRecord))
        graph.add((concept_uriref, hto.hadConceptRecord, item_uriref))


def add_summary(df_with_summary):
    for index, row in df_with_summary.iterrows():
        summary = row["summary"]
        if summary is not None and summary != "":
            print("add summary")
            description_uri = row["description_uri"]
            description_id = str(description_uri).split("/")[-1]
            description_uri = URIRef(description_uri)
            summary_uri = URIRef("https://w3id.org/hto/Summary/" + description_id)
            graph.add((summary_uri, RDF.type, hto.Summary))
            graph.add((description_uri, hto.hasSummary, summary_uri))
            graph.add((summary_uri, hto.text, Literal(summary, datatype=XSD.string)))


if __name__ == "__main__":
    # add term links
    # eb_df_with_concept_uris = pd.read_json("../eb_kg_hq_normalised_embeddings_concepts_dataframe", orient="index")
    # term_links(eb_df_with_concept_uris)
    # graph.serialize(format="turtle", destination="../results/extra_concepts_records_link.ttl")

    # add wikidata links
    # concept_wiki_df = pd.read_json("concept_wikidata_dataframe", orient="index")
    # external_link(concept_wiki_df)
    # graph.serialize(format="turtle", destination="../results/extra_concepts_wikidata_link.ttl")


    # add dbpedia links
    # concept_dbpedia_df = pd.read_json("concept_dbpedia_dataframe", orient="index")
    # external_link(concept_dbpedia_df)
    # graph.serialize(format="turtle", destination="../results/extra_concepts_dbpedia_link.ttl")

    # add summary
    eb_df = pd.read_json("../eb_kg_hq_dataframe", orient="index")
    add_summary(eb_df)
    graph.serialize(format="turtle", destination="../results/add_summary.ttl")