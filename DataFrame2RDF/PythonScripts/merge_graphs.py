from rdflib import Graph

# Create a new RDFLib Graph
graph = Graph()


def run_task(inputs):
    print("---- Start the merge graphs task ----")
    input_graphs_filenames = inputs["graphs_filenames"]
    for input_graph_filename in input_graphs_filenames:
        print(f"Parsing {input_graph_filename} ......")
        input_graph_filepath = "../../results/" + input_graph_filename
        graph.parse(input_graph_filepath, format="turtle")
        print(f"Finished parsing {input_graph_filename}")

    result_graph_filename = inputs["results_filenames"]["graph"]
    result_graph_filepath = "../../results/" + result_graph_filename
    # Save the Graph in the RDF Turtle format
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
