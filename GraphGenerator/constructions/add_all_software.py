from ..utils import all_software_list, add_software_with_name
from rdflib import Graph, Namespace, RDF, URIRef, Literal, XSD

hto = Namespace("https://w3id.org/hto#")

if __name__ == "__main__":
    # Load graph from file
    graph = Graph()
    graph_filepath = "hto.ttl"
    graph.parse(graph_filepath, format="turtle")
    add_software_with_name(all_software_list, graph)

    # Save the Graph in the RDF Turtle format
    result_graph_filepath = "results/all_software.ttl"
    print(f"Saving the result graph to {result_graph_filepath}....")
    graph.serialize(format="turtle", destination=result_graph_filepath)
