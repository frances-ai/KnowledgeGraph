import nltk
from rdflib import URIRef, RDF, Literal, XSD, Graph
from rdflib.plugins.sparql import prepareQuery
from tqdm import tqdm
from transformers import pipeline

from utils import hto

model_name = "Falconsai/text_summarization"
summarizer = pipeline("summarization", model=model_name)


def summarise_text_abstractive(text):
    # Spilt text into sentences, and the number of sentences should not be over max sentences
    MAX_SENTENCES = 100
    sentences = nltk.sent_tokenize(text)
    # print(len(sentences))
    if len(sentences) > MAX_SENTENCES:
        sentences = sentences[:MAX_SENTENCES]

    # print("chunking the text....")
    # Group sentences into small chunk of text whose token length should not be over max token length allowed by the model.
    tokenizer = summarizer.tokenizer
    max_token_length = tokenizer.model_max_length - 10
    # Split the input text into chunks of max_chunk_length
    chunks = []
    current_chunk = []

    # Chunk the sentences based on the maximum token length
    for sentence in sentences:
        tokenized_sentence = tokenizer.encode(sentence, add_special_tokens=False)
        if len(current_chunk) + len(tokenized_sentence) < max_token_length :
            current_chunk.extend(tokenized_sentence)
        else:
            chunks.append(current_chunk)
            current_chunk = list(tokenized_sentence)

    if current_chunk:
        chunks.append(current_chunk)

    # Convert token IDs back to text
    grouped_sentences = [''.join(tokenizer.decode(chunk)) for chunk in chunks]
    # print(f"text is chunked into {len(grouped_sentences)} pieces")

    summaries = []
    for index in range(0, len(grouped_sentences)):
        # Perform summarization on each chunk
        chunk = grouped_sentences[index]
        chunk_token_length = len(chunks[index])
        MAX_SUMMARY_LENGTH = 100
        MIN_LENGTH = 5
        if chunk_token_length < MIN_LENGTH * 2:
            continue
        if chunk_token_length < MAX_SUMMARY_LENGTH * 2:
            MAX_SUMMARY_LENGTH = int(chunk_token_length / 2)

        summary = summarizer(chunk, max_length=MAX_SUMMARY_LENGTH, min_length=MIN_LENGTH, do_sample=False)
        summaries.append(summary[0]['summary_text'])
    return ' '.join(summaries)


def get_description_uris_list(graph):
    q1 = prepareQuery('''
        SELECT ?description ?text WHERE {
            ?term a hto:TopicTermRecord;
                hto:hasOriginalDescription ?description.
            ?description hto:text ?text.
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
        graph_filepath = "../../results/" + graph_filename
        graph.parse(graph_filepath, format="turtle")
    print("The input graph is loaded!")

    print("Getting descriptions of topic term records from the graph....")
    uri_description_list = get_description_uris_list(graph)
    print("Got all the descriptions of topic term records from the graph!")

    print("Summarising the descriptions......")
    for index in tqdm(range(0, len(uri_description_list)), desc="Processing", unit="item"):
        description = uri_description_list[index]["description"]
        summary = summarise_text_abstractive(description)
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
        result_graph_filename = inputs["graph"]["name"]

    # Save the Graph in the RDF Turtle format
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
