import pandas as pd
from rdflib import Graph, RDF, URIRef, RDF, Literal, XSD, PROV, FOAF

from ..utils import remove_extra_spaces, hto, get_term_id_from_uri


neuspell = URIRef("https://github.com/neuspell/neuspell")


def get_uri_cleaned_definition(clean_dataframe, eb_total_nls_df_with_uris):
    cleaned_definitions = []
    for index in range(0, len(clean_dataframe)):
        MMSID = clean_dataframe.loc[index, "MMSID"]
        uri = eb_total_nls_df_with_uris[(eb_total_nls_df_with_uris["MMSID"] == MMSID) & (eb_total_nls_df_with_uris["id"] == index)]["uri"].iloc[0]
        cleaned_definitions.append({
            "uri": uri,
            "definition": remove_extra_spaces(clean_dataframe.loc[index, "definition"])
        })
    return cleaned_definitions


def add_definition_and_source_to_graph(clean_definitions, graph):
    for clean_definition in clean_definitions:
        uri = clean_definition["uri"]
        definition = clean_definition["definition"]
        term_uri_ref = URIRef(uri)
        term_id = get_term_id_from_uri(uri)
        definition_uri_ref = URIRef("https://w3id.org/hto/OriginalDescription/" + term_id + "Neuspell")
        graph.add((definition_uri_ref, RDF.type, hto.OriginalDescription))
        graph.add((definition_uri_ref, hto.hasTextQuality, hto.Moderate))
        graph.add((definition_uri_ref, hto.text, Literal(definition, datatype=XSD.string)))
        graph.add((definition_uri_ref, PROV.wasAttributedTo, neuspell))
        graph.add((term_uri_ref, hto.hasOriginalDescription, definition_uri_ref))
        nls_definition_uri_ref = URIRef("https://w3id.org/hto/OriginalDescription/" + term_id + "NLS")
        graph.add((definition_uri_ref, PROV.wasDerivedFrom, nls_definition_uri_ref))


def run_task(inputs):
    print("---- Start neuspell corrected eb to rdf task ----")
    print("Loading the input graph....")
    input_graph = inputs["graph"]
    if "object" in input_graph:
        graph = input_graph["object"]
    else:
        # Create a new RDFLib Graph
        graph = Graph()
        # Load your ontology file into the graph
        graph_filename = input_graph["filename"]
        graph_filepath = graph_filename
        graph.parse(graph_filepath, format="turtle")
    print("The input graph is loaded!")

    graph.add((neuspell, RDF.type, hto.SoftwareAgent))
    graph.add((neuspell, FOAF.name, Literal("Neuspell", datatype=XSD.string)))

    # load dataframe_with_uris generated from eb_total_nls_df_with_uris task
    input_dataframe_with_uri = inputs["dataframe_with_uris"]
    if "object" in input_dataframe_with_uri:
        eb_total_nls_df_with_uris = input_dataframe_with_uri["object"]
    else:
        input_dataframe_with_uri_filename = input_dataframe_with_uri["filename"]
        input_dataframe_with_uri_filepath = "GraphGenerator/dataframe_with_uris/" + input_dataframe_with_uri_filename
        eb_total_nls_df_with_uris = pd.read_json(input_dataframe_with_uri_filepath, orient="index")

    eb_dataframes = inputs["dataframes"]
    for dataframe in eb_dataframes:
        filename = dataframe["filename"]
        file_path = "source_dataframes/eb/" + filename
        print(f"Parsing dataframe {filename} to graph....")
        df = pd.read_json(file_path, orient="index")

        df.rename(columns={"relatedTerms": "reference_terms", "typeTerm": "termType", "positionPage": "position",
                               "altoXML": "filePath"}, inplace=True)
        print("Getting corrected definitions and term uris......")
        corrected_definitions = get_uri_cleaned_definition(df, eb_total_nls_df_with_uris)
        print("Adding corrected definitions to the graph......")
        add_definition_and_source_to_graph(corrected_definitions, graph)
        print("Corrected definitions are added to the graph!")


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