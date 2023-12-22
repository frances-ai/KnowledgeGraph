import pandas as pd
from rdflib import Graph, URIRef, RDFS
from rdflib import Literal, XSD, RDF
from rdflib.namespace import FOAF, PROV, SDO
from utils import hto, name_to_uri_name, frances_information_extraction, defoe, add_software, create_organization, \
    create_dataset

# Create a new RDFLib Graph
graph = Graph()

ontology_file = "../../hto.ttl"
graph.parse(ontology_file, format="turtle")


def create_collection():
    collection = URIRef("https://w3id.org/hto/WorkCollection/ChapbooksOfScotland")
    graph.add((collection, RDF.type, hto.WorkCollection))
    graph.add((collection, hto.name, Literal("Chapbooks printed in Scotland Collection", datatype=XSD.string)))
    return collection


collection = create_collection()


def series2rdf(series_info):
    # create triples with general datatype
    series = URIRef("https://w3id.org/hto/Series/" + str(series_info["MMSID"]))
    series_title = str(series_info["serieTitle"])
    graph.add((series, RDF.type, hto.Series))
    graph.add((collection, hto.hadMember, series))
    graph.add((series, hto.number, Literal(int(series_info["serieNum"]), datatype=XSD.integer)))
    graph.add((series, hto.title, Literal(series_title, datatype=XSD.string)))
    series_sub_title = str(series_info["serieSubTitle"])
    if series_sub_title != "0":
        graph.add((series, hto.subtitle, Literal(series_sub_title, datatype=XSD.string)))

    publish_year = str(series_info["year"])
    if publish_year != "0":
        graph.add((series, hto.yearPublished, Literal(publish_year, datatype=XSD.int)))
    # create a Location instance for printing place
    place_name = str(series_info["place"])
    if place_name != "0":
        place_uri_name = name_to_uri_name(place_name)
        place = URIRef("https://w3id.org/hto/Location/" + place_uri_name)
        graph.add((place, RDF.type, hto.Location))
        graph.add((place, RDFS.label, Literal(place_name, datatype=XSD.string)))
        graph.add((series, hto.printedAt, place))

    graph.add((series, hto.mmsid, Literal(str(series_info["MMSID"]), datatype=XSD.string)))
    graph.add((series, hto.physicalDescription, Literal(series_info["physicalDescription"], datatype=XSD.string)))
    graph.add((series, hto.genre, Literal(series_info["genre"], datatype=XSD.string)))
    graph.add((series, hto.language, Literal(series_info["language"], datatype=XSD.language)))

    # create a Location instance for shelf locator
    shelf_locator_name = str(series_info["shelfLocator"])
    shelf_locator_uri_name = name_to_uri_name(shelf_locator_name)
    shelf_locator = URIRef("https://w3id.org/hto/Location/" + shelf_locator_uri_name)
    graph.add((shelf_locator, RDF.type, hto.Location))
    graph.add((shelf_locator, RDFS.label, Literal(shelf_locator_name, datatype=XSD.string)))
    graph.add((series, hto.shelfLocator, shelf_locator))

    ## Editor
    if series_info["editor"] != 0:
        editor_name = str(series_info["editor"])
        editor_uri_name = name_to_uri_name(editor_name)
        if editor_name != "":
            editor = URIRef("https://w3id.org/hto/Person/" + str(editor_uri_name))
            graph.add((editor, RDF.type, hto.Person))
            graph.add((editor, FOAF.name, Literal(editor_name, datatype=XSD.string)))

        if series_info["editor_date"] != 0:
            editor_date = str(series_info["editor_date"]).replace("?", "")
            if editor_date.find("-") != -1:
                tmpDate = editor_date.split("-")

                birthYear = tmpDate[0]
                deathYear = tmpDate[1]

                if birthYear.isnumeric():
                    graph.add((editor, hto.birthYear, Literal(int(birthYear), datatype=XSD.int)))
                if deathYear.isnumeric():
                    graph.add((editor, hto.deathYear, Literal(int(deathYear), datatype=XSD.int)))
            else:
                print(f"date {editor_date} cannot be parsed!")

        if series_info["termsOfAddress"] != 0:
            graph.add((editor, hto.termsOfAddress, Literal(series_info["termsOfAddress"], datatype=XSD.string)))

        graph.add((series, hto.editor, editor))

    #### Publishers Persons

    # This was the result to pass entity recognition to publisher

    if series_info["publisherPersons"] != 0 and len(series_info["publisherPersons"]) > 0:
        publisherPersons = series_info["publisherPersons"]
        #print(publisherPersons)
        if len(publisherPersons) == 1:
            publisher_name = publisherPersons[0]
            iri_publisher_name = name_to_uri_name(publisher_name)
            if iri_publisher_name != "":
                publisher = URIRef("https://w3id.org/hto/Person/" + iri_publisher_name)
                graph.add((publisher, RDF.type, hto.Person))
        else:
            iri_publisher_name = ""
            publisher_name = ""
            for p in publisherPersons:
                publisher_name = publisher_name + ", " + p
                iri_publisher_name = name_to_uri_name(publisher_name)
                if iri_publisher_name == "":
                    break
            publisher = URIRef("https://w3id.org/hto/Organization/" + iri_publisher_name)
            graph.add((publisher, RDF.type, hto.Organization))

        graph.add((publisher, FOAF.name, Literal(publisher_name, datatype=XSD.string)))
        graph.add((series, hto.publisher, publisher))

        # Creat an instance of publicationActivity
        # publication_activity = URIRef("https://w3id.org/hto/Activity/"+ "publication" + str(series_info["MMSID"]))
        # graph.add((publication_activity, RDF.type, PROV.Activity))
        # graph.add((publication_activity, PROV.generated, series))
        #  if publish_year != "0":
        # graph.add((publication_activity, PROV.endedAtTime, Literal(publish_year, datatype=XSD.dateTime)))
        # graph.add((publication_activity, PROV.wasEndedBy, publisher))

        # graph.add((series, PROV.wasGeneratedBy, publication_activity))

    #### Is Referenced by

    if series_info["referencedBy"] != 0:
        references = series_info["referencedBy"]
        for r in references:
            book_name = str(r)
            book_uri_name = name_to_uri_name(book_name)
            book = URIRef("https://w3id.org/hto/Book/" + book_uri_name)
            graph.add((book, RDF.type, SDO.Book))
            graph.add((book, hto.name, Literal(book_name, datatype=XSD.string)))
            graph.add((series, hto.referencedBy, book))

    return series


def volume2rdf(volume_info, series):
    volume_id = str(volume_info["volumeId"])
    volume = URIRef("https://w3id.org/hto/Volume/" + str(volume_info["MMSID"]) + "_" + str(volume_id))
    graph.add((volume, RDF.type, hto.Volume))
    graph.add((volume, hto.number, Literal(volume_info["volumeNum"], datatype=XSD.integer)))
    graph.add((volume, hto.volumeId, Literal(volume_id, datatype=XSD.string)))
    graph.add((volume, hto.title, Literal(volume_info["volumeTitle"], datatype=XSD.string)))

    if volume_info["part"] != 0:
        graph.add((volume, hto.part, Literal(volume_info["part"], datatype=XSD.integer)))

    permanentURL = URIRef(str(volume_info["permanentURL"]))
    graph.add((permanentURL, RDF.type, hto.Location))
    graph.add((volume, hto.permanentURL, permanentURL))
    # graph.add((volume, hto.numberOfPages, Literal(volume_info["numberOfPages"], datatype=XSD.integer)))
    graph.add((series, RDF.type, hto.WorkCollection))
    graph.add((series, hto.hadMember, volume))
    graph.add((volume, hto.wasMemberOf, series))

    return volume


def dataframe_to_rdf(dataframe, agent_uri, agent, chapbook_dataset):
    dataframe = dataframe.fillna(0)
    # create triples
    series_mmsids = dataframe["MMSID"].unique()
    for mmsid in series_mmsids:
        df_series = dataframe[dataframe["MMSID"] == mmsid].reset_index(drop=True)
        edition_info = df_series.loc[0]
        #print(edition_info["serieTitle"])
        edition_ref = series2rdf(edition_info)

        # VOLUMES
        vol_numbers = df_series["volumeNum"].unique()
        # graph.add((edition_ref, hto.numberOfVolumes, Literal(len(vol_numbers), datatype=XSD.integer)))
        for vol_number in vol_numbers:
            df_vol = df_series[df_series["volumeNum"] == vol_number].reset_index(drop=True)
            volume_info = df_vol.loc[0]
            volume_ref = volume2rdf(volume_info, edition_ref)
            # print(volume_info)

            #### Pages
            for df_vol_index in range(0, len(df_vol)):
                df_page = df_vol.loc[df_vol_index]
                page_num = int(df_page["pageNum"])
                page_id = str(df_page["MMSID"]) + "_" + str(df_page["volumeId"]) + "_" + str(page_num)
                page_uri = URIRef("https://w3id.org/hto/Page/" + page_id)
                graph.add((page_uri, RDF.type, hto.Page))

                # Create original description for the page
                description = str(df_page["text"])
                if description != "":
                    page_original_description = URIRef("https://w3id.org/hto/OriginalDescription/" + page_id + agent)
                    graph.add((page_original_description, RDF.type, hto.OriginalDescription))
                    graph.add((page_original_description, hto.hasTextQuality, hto.Low))
                    graph.add((page_original_description, hto.text, Literal(description, datatype=XSD.string)))
                    graph.add((page_uri, hto.hasOriginalDescription, page_original_description))
                    graph.add((volume_ref, hto.hadMember, page_uri))
                    graph.add((page_original_description, PROV.wasAttributedTo, frances_information_extraction))

                    # Create source entity where original description was extracted
                    # source location
                    # source_path_name = df_entry["altoXML"]
                    # source_path_ref = URIRef("https://w3id.org/eb/Location/" + source_path_name)
                    # graph.add((source_path_ref, RDF.type, PROV.Location))
                    # source
                    source_name = df_page["altoXML"].replace("/", "_").replace(".", "_")
                    source_ref = URIRef("https://w3id.org/hto/InformationResource/" + source_name)
                    graph.add((source_ref, RDF.type, hto.InformationResource))
                    graph.add((chapbook_dataset, hto.hadMember, source_ref))
                    # graph.add((source_ref, PROV.atLocation, source_path_ref))
                    # related agent and activity
                    graph.add((source_ref, PROV.wasAttributedTo, agent_uri))
                    graph.add((source_ref, PROV.wasAttributedTo, defoe))

                    """
                    source_digitalising_activity = URIRef("https://w3id.org/eb/Activity/nls_digitalising_activity" + source_name)
                    graph.add((source_digitalising_activity, RDF.type, PROV.Activity))
                    graph.add((source_digitalising_activity, PROV.generated, source_ref))
                    graph.add((source_digitalising_activity, PROV.wasAssociatedWith, nls))
                    graph.add((source_ref, PROV.wasGeneratedBy, source_digitalising_activity))
                    """
                    graph.add((page_original_description, hto.wasExtractedFrom, source_ref))

    return graph


def run_task(inputs):
    print("---- Start the chapbook dataframe to rdf task ----")
    chapbook_dataframes = inputs["dataframes"]
    # dataframe = [{"agent": "NLS", "filename": ""}]

    # add software agents to graph
    software_list = [defoe, frances_information_extraction]
    add_software(software_list, graph)

    for dataframe in chapbook_dataframes:
        filename = dataframe["filename"]
        file_path = "../../source_dataframes/chapbooks/" + filename
        print(f"Parsing dataframe {filename} to graph....")
        agent = dataframe["agent"]
        agent_uri = create_organization(agent, graph)
        eb_dataset = create_dataset("chapbook", agent_uri, agent, graph)
        df = pd.read_json(file_path, orient="index")

        dataframe_to_rdf(df, agent_uri, agent, eb_dataset)

        print(f"Finished parsing dataframe {filename} to graph!")

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
