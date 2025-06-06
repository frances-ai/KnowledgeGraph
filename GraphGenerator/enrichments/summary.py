from rdflib import URIRef, RDF, Literal, XSD, Graph
from rdflib.plugins.sparql import prepareQuery
from tqdm import tqdm
import nltk

from ..utils import hto
from summarizer import TransformerSummarizer
import os


os.environ["TOKENIZERS_PARALLELISM"] = "false"


def reduce_text_size(text):
    MAX_SENTENCES = 100
    # Tokenize the text into sentences using NLTK
    sentences = nltk.sent_tokenize(text)
    print(len(sentences))
    if len(sentences) > MAX_SENTENCES:
        reduced_text = ' '.join(sentences[:MAX_SENTENCES])
        return reduced_text
    else:
        return text


def summarize_text_extractive(text, extractive_model):
    text = reduce_text_size(text)
    summary = ''.join(extractive_model(text, min_length=60, max_length=300))
    return summary


def get_description_uris_list(graph):
    q1 = prepareQuery('''
        SELECT ?description ?text WHERE {
            ?term a hto:TopicTermRecord;
                hto:hasOriginalDescription ?description.
            ?description hto:text ?text;
                hto:hasTextQuality ?textQuality.
            FILTER NOT EXISTS {
              ?term hto:hasOriginalDescription [hto:hasTextQuality [hto:isTextQualityHigherThan ?textQuality]].
            }
        }
      ''', initNs={"hto": hto}
                      )

    uri_description_list = []
    for r in graph.query(q1):
        uri_description = {
            "description_uri": r.description,
            "description": str(r.text),
            "summary": None
        }
        uri_description_list.append(uri_description)

    return uri_description_list


def run_task(inputs):
    extractive_model = TransformerSummarizer(transformer_type="XLNet", transformer_model_key="xlnet-base-cased")
    print("---- Start summary task ----")
    print("Loading the input graph....")
    input_graph = inputs["graph"]
    if "object" in input_graph:
        graph = input_graph["object"]
    else:
        # Create a new RDFLib Graph
        graph = Graph()
        # Load your ontology file into the graph
        graph_filename = input_graph["filename"]
        graph_filepath = "results/" + graph_filename
        graph.parse(graph_filepath, format="turtle")
    print("The input graph is loaded!")

    print("Getting descriptions of topic term records from the graph....")
    uri_description_list = get_description_uris_list(graph)
    print("Got all the descriptions of topic term records from the graph!")

    print("Summarising the descriptions......")
    for index in tqdm(range(0, len(uri_description_list)), desc="Processing", unit="item"):
        description = uri_description_list[index]["description"]
        summary = summarize_text_extractive(description)
        uri_description_list[index]["summary"] = summary
    print("Finished summarising the descriptions!")

    print("Adding summaries to the graph......")
    for uri_description in uri_description_list:
        summary = uri_description["summary"]
        if summary is not None and summary != "":
            description_uri = uri_description["description_uri"]
            description_id = str(description_uri).split("/")[-1]
            summary_uri = URIRef("https://w3id.org/hto/Summary/" + description_id)
            graph.add((summary_uri, RDF.type, hto.Summary))
            graph.add((description_uri, hto.hasSummary, summary_uri))
            graph.add((summary_uri, hto.text, Literal(summary, datatype=XSD.string)))
    print("All summaries are added to the graph!")

    if "results_filenames" in inputs:
        result_graph_filename = inputs["results_filenames"]["graph"]
    else:
        result_graph_filename = inputs["graph"]["filename"]

    # Save the Graph in the RDF Turtle format
    result_graph_filepath = "results/" + result_graph_filename
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
