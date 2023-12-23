from rdflib import URIRef, Graph
from rdflib.plugins.sparql import prepareQuery
from sentence_transformers import SentenceTransformer, util

from utils import hto

model_name = 'all-mpnet-base-v2'

model = SentenceTransformer(model_name)


def paraphrases_mining(descriptions):
    return util.paraphrase_mining(model, descriptions, corpus_chunk_size=len(descriptions), top_k=20,
                                  show_progress_bar=True)


def get_descriptions_term_uris_list(graph):
    # Get all original description with the highest text quality of terms, along with the uri of the term.
    q1 = prepareQuery('''
        SELECT ?term ?text WHERE {
        ?term a ?termType;
            hto:hasOriginalDescription ?desc.
        ?desc hto:text ?text.
    	FILTER NOT EXISTS {
              ?term hto:hasOriginalDescription [hto:hasTextQuality [hto:isTextQualityHigherThan ?textQuality]].
            }
        FILTER (?termType = hto:ArticleTermRecord || ?termType = hto:TopicTermRecord)
      }
      ''', initNs={"hto": hto}
    )

    term_uris = []
    descriptions = []
    for r in graph.query(q1):
        term_uri = r.term
        description = r.text
        MAX_LENGTH = 10000
        if len(description) > MAX_LENGTH:
            description = description[:MAX_LENGTH]
            #print(f"----\n{description}\n")

        descriptions.append(description)
        term_uris.append(term_uri)

    return term_uris, descriptions


def run_task(inputs):
    print("---- Start similar terms task ----")
    print("Loading the input graph....")
    input_graph = inputs["graph"]
    if "object" in input_graph:
        graph = input_graph["object"]
    else:
        # Create a new RDFLib Graph
        graph = Graph()
        # Load your ontology file into the graph
        graph_filename = input_graph["filename"]
        graph_filepath = "../../results/" + graph_filename
        graph.parse(graph_filepath, format="turtle")
    print("The input graph is loaded!")

    print("Getting all original description with the highest text quality of terms....")
    term_uris, descriptions = get_descriptions_term_uris_list(graph)
    print("Got all the descriptions!")

    print("Paraphrasing the descriptions......")
    paraphrases = paraphrases_mining(descriptions)
    print("Finished paraphrasing the descriptions!")

    print("Linking similar terms......")
    for paraphrase in paraphrases:
        score, i, j = paraphrase
        threshold = 0.5
        if i != j and score > threshold:
            graph.add((URIRef(term_uris[i]), hto.similarTo, URIRef(term_uris[j])))
    print("Finished linking similar terms!")

    if "results_filenames" in inputs:
        result_graph_filename = inputs["results_filenames"]["graph"]
    else:
        result_graph_filename = inputs["graph"]["name"]

    # Save the Graph in the RDF Turtle format
    result_graph_filename = inputs["results_filenames"]["graph"]
    result_graph_filepath = "../../results/" + result_graph_filename
    print(f"Saving the result graph to {result_graph_filepath}....")
    graph.serialize(format="turtle", destination=result_graph_filepath)
    print("Finished saving the result graph!")
    outputs = {
        "graph": {
            "filename": result_graph_filename,
            "object": graph
        }
    }

    return outputs
