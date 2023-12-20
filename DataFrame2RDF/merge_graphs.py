from rdflib import Graph, URIRef, Namespace

# Create a new RDFLib Graph
graph = Graph()


if __name__ == "__main__":
    # Load your ontology file into the graph
    chapbooks_kg = "../results/hto_chapbooks_nls.ttl"
    eb_total = "../results/hto_eb_total.ttl"

    print(f"Parsing chapbooks kg ......")
    graph.parse(chapbooks_kg, format="turtle")
    print(f"Finished parsing chapbooks kg!")
    print(f"Graph g has {len(graph)} statements.")

    print(f"Parsing eb_total ......")
    graph.parse(eb_total, format="turtle")
    print(f"Finished parsing eb_total ......")
    print(f"Graph g has {len(graph)} statements.")

    # Save the Graph in the RDF Turtle format
    print("Saving the merged graph ......")
    graph.serialize(format="turtle", destination="../results/hto_total.ttl")
    print("The merged graph is saved!")
