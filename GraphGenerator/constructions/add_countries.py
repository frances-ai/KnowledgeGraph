import pandas as pd
from rdflib import Graph, URIRef, RDF, XSD
from rdflib import RDFS, Literal
from rdflib.namespace import GEO
import string
from ..utils import crm, hto, name_to_uri_name
from shapely.geometry import shape
import json

def normalize_entity_name(entity_name):
    # Capitalize each word in the name
    return string.capwords(entity_name)

def add_centroid(location, location_id, target_graph):
    centroid_uri = URIRef("https://w3id.org/hto/SP6_Declarative_Place/" + location_id + "/centroid")
    target_graph.add((centroid_uri, RDF.type, crm.SP6_Declarative_Place))
    geojson = Literal(
        '''{"type": "Point", "coordinates": [%s, %s]}''' % (location["longitude"], location["latitude"]),
        datatype=GEO.geoJSONLiteral)
    target_graph.add((centroid_uri, GEO.asGeoJSON, geojson))
    wkt = Literal(
        '''POINT(%s %s)''' % (location["latitude"], location["longitude"]),
        datatype=GEO.wktLiteral)
    target_graph.add((centroid_uri, GEO.asWKT, wkt))
    return centroid_uri

def add_boundary(location, location_id, target_graph):
    boundary_uri = URIRef("https://w3id.org/hto/SP6_Declarative_Place/" + location_id + "/boundary")
    target_graph.add((boundary_uri, RDF.type, crm.SP6_Declarative_Place))
    geojson_str = location['boundary']
    geojson = Literal(
        geojson_str,
        datatype=GEO.geoJSONLiteral)
    target_graph.add((boundary_uri, GEO.asGeoJSON, geojson))
    geojson_data = json.loads(geojson_str)
    # convert geojson_data to wkt
    wkt_str = shape(geojson_data).wkt
    wkt = Literal(
        wkt_str,
        datatype=GEO.wktLiteral)
    target_graph.add((boundary_uri, GEO.asWKT, wkt))
    return boundary_uri

def add_phenomenal_place(location, target_graph):
    """
    This function constructs phenomenal place for a country location and add to graph. It also creates the centroid, boundary and links them with the phenomenal place. It returns the uri of the added phenomenal place.
    :param location: location details used to construct phenomenal place.
    :param target_graph: the targe knowledge graph.
    :return: location_uri: an id and an URIRef of the added phenomenal place.
    """
    normalized_name = normalize_entity_name(location["name"])
    location_id = name_to_uri_name(normalized_name)
    if "latitude" in location and location["latitude"]:
        latitude = location["latitude"]
        longitude = location["longitude"]
        latitude = round(latitude, 5)
        longitude = round(longitude, 5)
        lat_str = str(latitude).replace('.', 'd')
        lon_str = str(longitude).replace('.', 'd')
        location_id += "_" + lat_str + "_" + lon_str

    location_uri = URIRef("https://w3id.org/hto/SP2_Phenomenal_Place/" + location_id)
    location["uri"] = location_uri

    target_graph.add((location_uri, RDF.type, crm.SP2_Phenomenal_Place))
    target_graph.add((location_uri, RDFS.label, Literal(normalized_name, datatype=XSD.string)))

    # link location type
    target_graph.add((location_uri, hto.hasLocationType, hto.Country))

    # add area
    target_graph.add((location_uri, GEO.hasMetricArea, Literal(float(location["area"]), datatype=XSD.double)))

    # add centroid
    if "latitude" in location and location["latitude"]:
        centroid_uri = add_centroid(location, location_id, target_graph)
        target_graph.add((location_uri, GEO.hasCentroid, centroid_uri))

    # add boundary
    if "boundary" in location and location["boundary"]:
        boundary_uri = add_boundary(location, location_id, target_graph)
        target_graph.add((location_uri, GEO.hasGeometry, boundary_uri))
        target_graph.add((location_uri, GEO.defaultGeometry, boundary_uri))

    return location_uri


def run_task(inputs):
    print("---- Start the add countries task ----")

    # Load all the countries
    print("Loading the input countries dataframe....")
    countries_filename = inputs["dataframe"]
    countries_info_df = pd.read_json(countries_filename, orient='records', lines=True)
    print(f"{len(countries_info_df)} countries loaded.")

    print("Loading the input graph....")
    input_graph = inputs["graph"]
    if "object" in input_graph:
        graph = input_graph["object"]
    else:
        # Load graph from file
        graph = Graph()
        graph_filename = input_graph["filename"]
        graph_filepath = "results/" + graph_filename
        graph.parse(graph_filepath, format="turtle")
    print("The input graph is loaded!")

    print("Adding countries to graph...")
    countries_uris = []
    for index, location in countries_info_df.iterrows():
        location_uri = add_phenomenal_place(location, graph)
        countries_uris.append(str(location_uri))
    countries_info_df["uri"] = countries_uris

    countries_in_graph_df = countries_info_df[['name', 'uri', 'code', 'latitude', 'longitude']].reset_index(drop=True)

    result_dataframe_with_uris_filename = inputs["results_filenames"]["dataframe_with_uris"]
    dataframe_with_uris_filepath = 'GraphGenerator/dataframe_with_uris/' + result_dataframe_with_uris_filename
    # store the new dataframe with uris
    print(f"Saving dataframe with uris to {dataframe_with_uris_filepath} ....")
    countries_in_graph_df.to_json(dataframe_with_uris_filepath, orient="records", lines=True)
    print("Finished saving dataframe!")

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
        },
        "dataframe_with_uris": {
            "filename": result_dataframe_with_uris_filename,
            "object": countries_in_graph_df
        },
    }

    return outputs