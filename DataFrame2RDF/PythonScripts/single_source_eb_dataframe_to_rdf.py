from rdflib import Graph, URIRef, FOAF, PROV, SDO
import pandas as pd
from rdflib import Literal, XSD, RDF, RDFS
from utils import name_to_uri_name, get_source_ref, link_entity_with_software, hto, create_organization, \
    create_dataset, link_reference_terms, add_software, get_term_class_name_and_term_ref, defoe, \
    frances_information_extraction, ABBYYFineReader

# Create a new RDFLib Graph
graph = Graph()

# Load your ontology file into the graph
ontology_file = "../../hto.ttl"
graph.parse(ontology_file, format="turtle")

# load metadata
metadata_df = pd.read_json("../../source_dataframes/eb/nls_metadata_dataframe", orient="index")


def create_collection():
    collection = URIRef("https://w3id.org/hto/WorkCollection/EncyclopaediaBritannica")
    graph.add((collection, RDF.type, hto.WorkCollection))
    graph.add((collection, hto.name, Literal("Encyclopaedia Britannica Collection", datatype=XSD.string)))
    return collection


collection = create_collection()


# create edition uri list based on edition number
def get_edition_uri_by_number():
    edition_uris = {}
    metadata_df_without_supplement = metadata_df[metadata_df["editionNum"] > 0]
    edition_nums = metadata_df_without_supplement["editionNum"].unique()
    for edition_num in edition_nums:
        edition_df = metadata_df_without_supplement[metadata_df_without_supplement["editionNum"] == edition_num]
        edition_df = edition_df.iloc[0]
        edition_uri = URIRef("https://w3id.org/hto/Edition/" + str(edition_df["MMSID"]))
        edition_uris[edition_num] = edition_uri

    return edition_uris


edition_uris = get_edition_uri_by_number()


def edition2rdf(edition_info):
    # create triples with general datatype
    edition = URIRef("https://w3id.org/hto/Edition/" + str(edition_info["MMSID"]))
    graph.add((edition, RDF.type, hto.Edition))
    graph.add((collection, hto.hadMember, edition))

    # check if it is supplement edition
    supplmentsTo = edition_info["supplementsTo"]
    edition_num = int(edition_info["editionNum"])
    if edition_num == 0 and len(supplmentsTo) > 0 and supplmentsTo[0] != '':
        edition_title = str(edition_info["supplementTitle"])
        subtitle = edition_info["supplementSubTitle"]
        for to_edition_num in supplmentsTo:
            if to_edition_num in edition_uris.keys():
                to_edition_uri = edition_uris[to_edition_num]
                graph.add((edition, hto.wasSupplementOf, to_edition_uri))
    else:
        edition_title = str(edition_info["editionTitle"])
        subtitle = edition_info["editionSubTitle"]
        graph.add((edition, hto.number, Literal(edition_num, datatype=XSD.int)))

    graph.add((edition, hto.title, Literal(edition_title, datatype=XSD.string)))
    if subtitle != 0 and subtitle != "":
        graph.add((edition, hto.subtitle, Literal(edition_info["editionSubTitle"], datatype=XSD.string)))

    # publish_year = datetime.strptime(str(edition_info["year"]), "%Y")
    graph.add((edition, hto.yearPublished, Literal(int(edition_info["year"]), datatype=XSD.int)))
    # create a Location instance for printing place
    place_name = str(edition_info["place"])
    place_uri_name = name_to_uri_name(place_name)
    place = URIRef("https://w3id.org/hto/Location/" + place_uri_name)
    graph.add((place, RDF.type, hto.Location))
    graph.add((place, RDFS.label, Literal(place_name, datatype=XSD.string)))
    graph.add((edition, hto.printedAt, place))

    graph.add((edition, hto.mmsid, Literal(str(edition_info["MMSID"]), datatype=XSD.string)))
    graph.add((edition, hto.physicalDescription, Literal(edition_info["physicalDescription"], datatype=XSD.string)))
    graph.add((edition, hto.genre, Literal(edition_info["genre"], datatype=XSD.string)))
    graph.add((edition, hto.language, Literal(edition_info["language"], datatype=XSD.string)))

    # create a Location instance for shelf locator
    shelf_locator_name = str(edition_info["shelfLocator"])
    shelf_locator_uri_name = name_to_uri_name(shelf_locator_name)
    shelf_locator = URIRef("https://w3id.org/hto/Location/" + shelf_locator_uri_name)
    graph.add((shelf_locator, RDF.type, hto.Location))
    graph.add((shelf_locator, RDFS.label, Literal(shelf_locator_name, datatype=XSD.string)))
    graph.add((edition, hto.shelfLocator, shelf_locator))

    ## Editor
    if edition_info["editor"] != 0:
        editor_name = str(edition_info["editor"])
        editor_uri_name = name_to_uri_name(editor_name)

        if edition_info["editor_date"] != 0:
            tmpDate = edition_info["editor_date"].split("-")
            birthYear = int(tmpDate[0])
            deathYear = int(tmpDate[1])

            if editor_name != "":
                editor = URIRef("https://w3id.org/hto/Person/" + str(editor_uri_name))
                graph.add((editor, RDF.type, hto.Person))
                graph.add((editor, FOAF.name, Literal(editor_name, datatype=XSD.string)))
                graph.add((editor, hto.birthYear, Literal(birthYear, datatype=XSD.int)))
                graph.add((editor, hto.deathYear, Literal(deathYear, datatype=XSD.int)))

                if edition_info["termsOfAddress"] != 0:
                    graph.add((editor, hto.termsOfAddress, Literal(edition_info["termsOfAddress"], datatype=XSD.string)))
                graph.add((edition, hto.editor, editor))

    #### Publishers Persons

    # This was the result to pass entity recognition to publisher

    if edition_info["publisherPersons"] != 0 and len(edition_info["publisherPersons"]) > 0:
        publisherPersons = edition_info["publisherPersons"]
        # print(publisherPersons)
        if len(publisherPersons) == 1:
            publisher_name = publisherPersons[0]
            iri_publisher_name = name_to_uri_name(publisher_name)
            if iri_publisher_name != "":
                publisher = URIRef("https://w3id.org/hto/Person/" + iri_publisher_name)
                graph.add((publisher, RDF.type, hto.Person))
                graph.add((publisher, FOAF.name, Literal(publisher_name, datatype=XSD.string)))
                graph.add((edition, hto.publisher, publisher))
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
            graph.add((edition, hto.publisher, publisher))

        # Creat an instance of publicationActivity
        # publication_activity = URIRef("https://w3id.org/hto/Activity/"+ "publication" + str(edition_info["MMSID"]))
        # graph.add((publication_activity, RDF.type, PROV.Activity))
        # graph.add((publication_activity, PROV.generated, edition))
        # graph.add((publication_activity, PROV.endedAtTime, Literal(publish_year, datatype=XSD.dateTime)))
        # graph.add((publication_activity, PROV.wasEndedBy, publisher))
        # graph.add((edition, PROV.wasGeneratedBy, publication_activity))

    #### Is Referenced by

    if edition_info["referencedBy"] != 0:
        references = edition_info["referencedBy"]
        for r in references:
            book_name = str(r)
            book_uri_name = name_to_uri_name(book_name)
            book = URIRef("https://w3id.org/hto/Book/" + book_uri_name)
            graph.add((book, RDF.type, SDO.Book))
            graph.add((book, hto.name, Literal(book_name, datatype=XSD.string)))
            graph.add((edition, hto.referencedBy, book))

    return edition


def volume2rdf(volume_info, edition):
    volume_id = str(volume_info["volumeId"])
    volume = URIRef("https://w3id.org/hto/Volume/" + str(volume_info["MMSID"]) + "_" + str(volume_id))
    graph.add((volume, RDF.type, hto.Volume))
    graph.add((volume, hto.number, Literal(volume_info["volumeNum"], datatype=XSD.integer)))
    if volume_info["letters"] != 0 and volume_info["letters"] != "":
        graph.add((volume, hto.letters, Literal(volume_info["letters"], datatype=XSD.string)))
    graph.add((volume, hto.volumeId, Literal(volume_id, datatype=XSD.string)))
    graph.add((volume, hto.title, Literal(volume_info["volumeTitle"], datatype=XSD.string)))

    if volume_info["part"] != 0:
        graph.add((volume, hto.part, Literal(volume_info["part"], datatype=XSD.integer)))

    permanentURL = URIRef(str(volume_info["permanentURL"]))
    graph.add((permanentURL, RDF.type, hto.Location))
    graph.add((volume, hto.permanentURL, permanentURL))
    # graph.add((volume, hto.numberOfPages, Literal(volume_info["numberOfPages"], datatype=XSD.integer)))
    graph.add((edition, RDF.type, hto.WorkCollection))
    graph.add((edition, hto.hadMember, volume))
    graph.add((volume, hto.wasMemberOf, edition))

    return volume


previous_edition = {}


def dataframe_to_rdf(dataframe, agent_uri, agent, eb_dataset):
    dataframe = dataframe.fillna(0)
    dataframe["id"] = dataframe.index
    # create triples
    edition_mmsids = dataframe["MMSID"].unique()

    for mmsid in edition_mmsids:
        df_edition = dataframe[dataframe["MMSID"] == mmsid].reset_index(drop=True)

        edition_num = int(df_edition.loc[0, "editionNum"])
        year_published = int(df_edition.loc[0, "year"])

        tmp_edition_uri = URIRef("https://w3id.org/hto/Edition/" + str(mmsid))
        if (tmp_edition_uri, RDF.type, hto.Edition) in graph:
            continue

        # exchange the column volume title with edition title, note that this should be done when extract the metadata. This should be removed when it is fixed during information extraction.
        if edition_num > 0:
            df_edition.rename(columns={'editionTitle': 'volumeTitle', 'volumeTitle': 'editionTitle'}, inplace=True)

        edition_info = df_edition.loc[0]
        edition_ref = edition2rdf(edition_info)

        if edition_num != 0:
            # not supplement
            if edition_num in previous_edition.keys():
                # add revision info
                if previous_edition[edition_num]["year"] < year_published:
                    graph.add((edition_ref, PROV.wasRevisionOf, previous_edition[edition_num]["uri"]))
                elif previous_edition[edition_num]["year"] > year_published:
                    graph.add((previous_edition[edition_num]["uri"], PROV.wasRevisionOf, edition_ref))
            else:
                previous_edition[edition_num] = {
                    "year": year_published,
                    "uri": edition_ref
                }

        # VOLUMES
        vol_numbers = df_edition["volumeNum"].unique()
        # graph.add((edition_ref, hto.numberOfVolumes, Literal(len(vol_numbers), datatype=XSD.integer)))
        for vol_number in vol_numbers:
            df_vol = df_edition[df_edition["volumeNum"] == vol_number].reset_index(drop=True)
            volume_info = df_vol.loc[0]
            volume_ref = volume2rdf(volume_info, edition_ref)
            # print(volume_info)
            df_vol_by_term = df_vol.groupby(['term'], )["term"].count().reset_index(name='counts')
            # print(df_vol_by_term)

            #### TERMS
            for t_index in range(0, len(df_vol_by_term)):
                term = df_vol_by_term.loc[t_index]["term"]
                term_counts = df_vol_by_term.loc[t_index]["counts"]
                term_uri_name = name_to_uri_name(term)
                # print(term_uri_name)
                # All terms in one volume with name equals to value of term
                df_entries = df_vol[df_vol["term"] == term].reset_index(drop=True)
                for t_count in range(0, term_counts):
                    df_entry = df_entries.loc[t_count]
                    term_id = str(mmsid) + "_" + str(df_entry["volumeId"]) + "_" + term_uri_name + "_" + str(t_count)
                    term_type = str(df_entry["termType"]) + "TermRecord"

                    term_class_name, term_ref = get_term_class_name_and_term_ref(term_type, term_id)

                    # Add the term_ref to dataframe
                    dataframe_equal = (dataframe['id'] == df_entry['id'])
                    dataframe.loc[dataframe_equal, "uri"] = term_ref

                    graph.add((term_ref, RDF.type, term_class_name))
                    graph.add((term_ref, hto.name, Literal(term, datatype=XSD.string)))
                    if "note" in df_entry:
                        note = df_entry["note"]
                        if note != 0:
                            graph.add((term_ref, hto.note, Literal(note, datatype=XSD.string)))

                    if "alter_names" in df_entry:
                        alter_names = df_entry["alter_names"]
                        for alter_name in alter_names:
                            graph.add((term_ref, hto.name, Literal(alter_name, datatype=XSD.string)))

                    # Create original description instance
                    description = df_entry["definition"]
                    if description != "":

                        term_original_description = URIRef(
                            "https://w3id.org/hto/OriginalDescription/" + str(df_entry["MMSID"]) + "_" + str(
                                df_entry["volumeId"]) + "_" + term_uri_name + "_" + str(t_count) + agent)
                        graph.add((term_original_description, RDF.type, hto.OriginalDescription))
                        text_quality = hto.Low
                        if agent == "Ash":
                            text_quality = hto.Moderate
                        elif agent == "NCKP":
                            text_quality = hto.High
                        graph.add((term_original_description, hto.hasTextQuality, text_quality))
                        # graph.add((term_original_description, hto.numberOfWords, Literal(df_entry["numberOfWords"], datatype=XSD.int)))
                        graph.add(
                            (term_original_description, hto.text, Literal(df_entry["definition"], datatype=XSD.string)))

                        graph.add((term_ref, hto.hasOriginalDescription, term_original_description))
                        graph.add((term_ref, hto.position, Literal(df_entry["position"], datatype=XSD.int)))

                        link_entity_with_software(graph, term_original_description, "description", agent)

                        # Create source entity where original description was extracted
                        # source location
                        # source_path_name = df_entry["altoXML"]
                        # source_path_ref = URIRef("https://w3id.org/eb/Location/" + source_path_name)
                        # graph.add((source_path_ref, RDF.type, PROV.Location))
                        # source
                        file_path = str(df_entry["filePath"])
                        source_ref = get_source_ref(file_path, agent)
                        graph.add((source_ref, RDF.type, hto.InformationResource))
                        graph.add((source_ref, PROV.value, Literal(file_path, datatype=XSD.string)))
                        graph.add((eb_dataset, hto.hadMember, source_ref))
                        graph.add((source_ref, PROV.wasAttributedTo, agent_uri))
                        link_entity_with_software(graph, source_ref, "source", agent)

                        # graph.add((source_ref, PROV.atLocation, source_path_ref))
                        # related agent and activity

                        """
                        source_digitalising_activity = URIRef("https://w3id.org/eb/Activity/nls_digitalising_activity" + source_name)
                        graph.add((source_digitalising_activity, RDF.type, PROV.Activity))
                        graph.add((source_digitalising_activity, PROV.generated, source_ref))
                        graph.add((source_digitalising_activity, PROV.wasAssociatedWith, nls))
                        graph.add((source_ref, PROV.wasGeneratedBy, source_digitalising_activity))
                        """
                        graph.add((term_original_description, hto.wasExtractedFrom, source_ref))

                    ## startsAt
                    page_startsAt = URIRef("https://w3id.org/hto/Page/" + str(df_entry["MMSID"]) + "_" + str(
                        df_entry["volumeId"]) + "_" + str(df_entry["startsAt"]))
                    graph.add((page_startsAt, RDF.type, hto.Page))
                    graph.add((page_startsAt, hto.number, Literal(df_entry["startsAt"], datatype=XSD.int)))
                    if df_entry["header"] != 0 and df_entry["header"] != "":
                        graph.add((page_startsAt, hto.header, Literal(df_entry["header"], datatype=XSD.string)))
                    # graph.add((page_startsAt, hto.numberOfTerms, Literal(df_entry["numberOfTerms"], datatype=XSD.int)))
                    graph.add((volume_ref, RDF.type, hto.WorkCollection))
                    graph.add((volume_ref, hto.hadMember, page_startsAt))
                    graph.add((term_ref, hto.startsAtPage, page_startsAt))
                    graph.add((page_startsAt, RDF.type, hto.WorkCollection))
                    graph.add((page_startsAt, hto.hadMember, term_ref))

                    ## endsAt
                    page_endsAt = URIRef("https://w3id.org/hto/Page/" + str(df_entry["MMSID"]) + "_" + str(
                        df_entry["volumeId"]) + "_" + str(df_entry["endsAt"]))
                    graph.add((page_endsAt, RDF.type, hto.Page))
                    graph.add((page_endsAt, hto.number, Literal(df_entry["endsAt"], datatype=XSD.int)))
                    # graph.add((page_endsAt, hto.numberOfTerms, Literal(df_entry["numberOfTerms"], datatype=XSD.int)))
                    graph.add((volume_ref, hto.hadMember, page_endsAt))
                    graph.add((term_ref, hto.endsAtPage, page_endsAt))
                    graph.add((page_endsAt, RDF.type, hto.WorkCollection))
                    graph.add((page_endsAt, hto.hadMember, term_ref))

    return dataframe


def run_task(inputs):
    print("---- Start the single source eb dataframe to rdf task ----")
    eb_dataframes = inputs["dataframes"]
    # dataframe = [{"agent": "Ash", "filename": ""}]

    # add software agents to graph
    software_list = [defoe, frances_information_extraction, ABBYYFineReader]
    add_software(software_list, graph)

    dataframe_with_uris_list = []

    for dataframe in eb_dataframes:
        filename = dataframe["filename"]
        file_path = "../../source_dataframes/eb/" + filename
        print(f"Parsing dataframe {filename} to graph....")
        agent = dataframe["agent"]
        agent_uri = create_organization(agent, graph)
        eb_dataset = create_dataset("eb", agent_uri, agent, graph)
        df = pd.read_json(file_path, orient="index")

        if agent == "NLS":
            df.rename(columns={"relatedTerms": "reference_terms", "typeTerm": "termType", "positionPage": "position", "altoXML": "filePath"},
                      inplace=True)
        dataframe_with_uris = dataframe_to_rdf(df, agent_uri, agent, eb_dataset)
        dataframe_with_uris_list.append(dataframe_with_uris)

        print(f"Finished parsing dataframe {filename} to graph!")

    dataframe_with_uris_total = pd.concat(dataframe_with_uris_list, ignore_index=True)

    result_dataframe_with_uris_filename = inputs["results_filenames"]["dataframe_with_uris"]
    dataframe_with_uris_filepath = '../dataframe_with_uris/' + result_dataframe_with_uris_filename
    # store the new dataframe with uris
    print(f"Saving dataframe with uris to {dataframe_with_uris_filepath} ....")
    dataframe_with_uris_total.to_json(dataframe_with_uris_filepath, orient="index")
    print("Finished saving dataframe!")

    print("Linking reference terms.....")
    link_reference_terms(dataframe_with_uris_total, graph)
    print("Finished linking reference terms!")

    # Save the Graph in the RDF Turtle format
    result_graph_filename = inputs["results_filenames"]["graph"]
    result_graph_filepath = "../../results/" + result_graph_filename
    print(f"Saving the result graph to {result_graph_filepath}....")
    graph.serialize(format="turtle", destination=result_graph_filepath)
    print("Finished saving the result graph!")
    outputs = {
        "dataframe_with_uris": {
            "filename": result_dataframe_with_uris_filename,
            "object": dataframe_with_uris_total
        },
        "graph": {
            "filename": result_graph_filename,
            "object": graph
        }
    }

    return outputs
