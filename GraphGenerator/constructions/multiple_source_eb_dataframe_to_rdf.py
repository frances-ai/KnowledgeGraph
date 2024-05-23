import pandas as pd
from rdflib import Literal, XSD, RDF, RDFS, URIRef, Graph
from rdflib.namespace import FOAF, PROV, Namespace
from difflib import SequenceMatcher

from ..utils import name_to_uri_name, get_term_class_name, \
    get_source_ref, link_entity_with_software, hto, create_organization, create_dataset, \
    link_reference_terms, add_software, defoe, frances_information_extraction, ABBYYFineReader


def is_descriptions_for_same_term(description_1, description_2):
    MAX_COMPARE_LENGTH = 200
    if len(description_1) > MAX_COMPARE_LENGTH:
        description_1 = description_1[:MAX_COMPARE_LENGTH]
    if len(description_2) > MAX_COMPARE_LENGTH:
        description_2 = description_2[:MAX_COMPARE_LENGTH]

    similarity_ratio = SequenceMatcher(None, description_1, description_2).quick_ratio()

    threshold = 0.7

    if similarity_ratio >= threshold:
        return True
    else:
        len_1 = len(description_1)
        len_2 = len(description_2)
        recheck = False
        if len_1 > len_2:
            recheck = True
            description_1 = description_1[:len_2]
        elif len_2 > len_1:
            recheck = True
            description_2 = description_2[:len_1]
        if recheck:
            similarity_ratio = SequenceMatcher(None, description_1, description_2).quick_ratio()
            threshold = 0.85
            if similarity_ratio > threshold:
                return True
        return False


def find_existing_term(same_vol_term_name_in_graph, description):
    for index in range(0, len(same_vol_term_name_in_graph)):
        term_info_in_graph = same_vol_term_name_in_graph.loc[index]
        if not term_info_in_graph["match"]:
            description_in_graph = term_info_in_graph["definition"]
            if is_descriptions_for_same_term(description_in_graph, description):
                same_vol_term_name_in_graph.loc[index, "match"] = True
                return term_info_in_graph["uri"]
    return None


def dataframe_to_rdf(dataframe, graph, agent_uri, agent, eb_dataset, single_source_dataframe_with_uris):
    dataframe = dataframe.fillna(0)
    edition_mmsids = dataframe["MMSID"].unique()
    dataframe_with_uri_list = []
    for mmsid in edition_mmsids:
        df_edition = dataframe[dataframe["MMSID"] == mmsid]
        # VOLUMES
        vol_numbers = df_edition["volumeNum"].unique()
        for vol_number in vol_numbers:
            df_vol = df_edition[df_edition["volumeNum"] == vol_number].reset_index(drop=True)
            volume_info = df_vol.loc[0]
            volume_id = volume_info["volumeId"]
            volume_ref = URIRef("https://w3id.org/hto/Volume/" + str(volume_info["MMSID"]) + "_" + str(volume_id))

            df_vol_by_term = df_vol.groupby(['term'], )["term"].count().reset_index(name='counts')
            # print(df_vol_by_term)
            #### TERMS

            for t_index in range(0, len(df_vol_by_term)):
                term = df_vol_by_term.loc[t_index]["term"]
                term_counts = df_vol_by_term.loc[t_index]["counts"]
                term_uri_name = name_to_uri_name(term)

                same_vol_term_name_in_graph = single_source_dataframe_with_uris[
                    (single_source_dataframe_with_uris["volumeId"] == volume_id) & (
                                single_source_dataframe_with_uris["term"] == term)].reset_index(drop=True)
                same_vol_term_name_in_graph["match"] = False
                # print(term_uri_name)
                # All terms in one volume with name equals to value of term
                df_entries = df_vol[df_vol["term"] == term].reset_index(drop=True)
                new_term_count = 0
                len_same_vol_term_name_in_graph = len(same_vol_term_name_in_graph)
                for t_count in range(0, term_counts):
                    df_entry = df_entries.loc[t_count]
                    description = str(df_entry["definition"])
                    existing_term = find_existing_term(same_vol_term_name_in_graph, description)
                    term_type = str(df_entry["termType"]) + "TermRecord"
                    term_class_name = get_term_class_name(term_type, hto)
                    if existing_term:
                        term_id = existing_term.split("/")[-1]
                        term_ref = URIRef(existing_term)
                        # new description, new source
                    else:
                        # add new term record
                        term_id = str(mmsid) + "_" + str(df_entry["volumeId"]) + "_" + term_uri_name + "_" + str(
                            new_term_count + len_same_vol_term_name_in_graph)
                        term_ref = URIRef("https://w3id.org/hto/" + term_type + "/" + term_id)
                        graph.add((term_ref, RDF.type, term_class_name))
                        graph.add((term_ref, hto.name, Literal(term, datatype=XSD.string)))
                        graph.add((term_ref, hto.position, Literal(df_entry["position"], datatype=XSD.int)))

                        # Add the term_ref to dataframe
                        dataframe_new_term = df_entry.copy()
                        dataframe_new_term["uri"] = term_ref
                        dataframe_with_uri_list.append(dataframe_new_term)

                        ## startsAt
                        page_startsAt = URIRef("https://w3id.org/hto/Page/" + str(df_entry["MMSID"]) + "_" + str(
                            df_entry["volumeId"]) + "_" + str(df_entry["startsAt"]))
                        graph.add((page_startsAt, RDF.type, hto.Page))
                        graph.add((page_startsAt, hto.number, Literal(df_entry["startsAt"], datatype=XSD.int)))
                        graph.add((volume_ref, hto.hadMember, page_startsAt))
                        graph.add((term_ref, hto.startsAtPage, page_startsAt))
                        graph.add((page_startsAt, RDF.type, hto.WorkCollection))
                        graph.add((page_startsAt, hto.hadMember, term_ref))

                        ## endsAt
                        page_endsAt = URIRef("https://w3id.org/hto/Page/" + str(df_entry["MMSID"]) + "_" + str(
                            df_entry["volumeId"]) + "_" + str(df_entry["endsAt"]))
                        graph.add((page_endsAt, RDF.type, hto.Page))
                        graph.add((page_endsAt, hto.number, Literal(df_entry["endsAt"], datatype=XSD.int)))
                        graph.add((volume_ref, hto.hadMember, page_endsAt))
                        graph.add((term_ref, hto.endsAtPage, page_endsAt))
                        graph.add((page_endsAt, RDF.type, hto.WorkCollection))
                        graph.add((page_endsAt, hto.hadMember, term_ref))

                        new_term_count += 1
                        # new term, add new page, new description, new source

                    if "note" in df_entry:
                        note = df_entry["note"]
                        if note != 0:
                            graph.add((term_ref, hto.note, Literal(note, datatype=XSD.string)))

                    if "alter_names" in df_entry:
                        alter_names = df_entry["alter_names"]
                        for alter_name in alter_names:
                            graph.add((term_ref, RDFS.label, Literal(alter_name, datatype=XSD.string)))

                    # Create original description instance
                    term_original_description = URIRef(
                        "https://w3id.org/hto/OriginalDescription/" + term_id + agent)
                    graph.add((term_original_description, RDF.type, hto.OriginalDescription))
                    text_quality = hto.Low
                    if agent == "Ash":
                        text_quality = hto.High
                    elif agent == "NCKP":
                        text_quality = hto.High
                    graph.add((term_original_description, hto.hasTextQuality, text_quality))
                    # graph.add((term_original_description, hto.numberOfWords, Literal(df_entry["numberOfWords"], datatype=XSD.int)))
                    graph.add((term_original_description, hto.text, Literal(description, datatype=XSD.string)))
                    graph.add((term_ref, hto.hasOriginalDescription, term_original_description))
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

    dataframe_with_uris = pd.concat(dataframe_with_uri_list, axis=1).T.reset_index(drop=True)
    return graph, dataframe_with_uris


def run_task(inputs):
    print("---- Start the multiple source eb dataframe to rdf task ----")
    eb_dataframes = inputs["dataframes"]
    # dataframe = [{"agent": "Ash", "filename": ""}]

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

    # add software agents to graph
    software_list = [defoe, frances_information_extraction, ABBYYFineReader]
    add_software(software_list, graph)

    # load dataframe_with_uris generated from single_source_eb_dataframe_to_rdf task
    input_dataframe_with_uri = inputs["dataframe_with_uris"]
    if "object" in input_dataframe_with_uri:
        single_source_dataframe_with_uris = input_dataframe_with_uri["object"]
    else:
        input_dataframe_with_uri_filename = input_dataframe_with_uri["filename"]
        input_dataframe_with_uri_filepath = "../dataframe_with_uris/" + input_dataframe_with_uri_filename
        single_source_dataframe_with_uris = pd.read_json(input_dataframe_with_uri_filepath, orient="index")

    new_terms_dataframe_with_uris_list = []

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
        graph, dataframe_with_uris = dataframe_to_rdf(df, graph, agent_uri, agent, eb_dataset, single_source_dataframe_with_uris)
        new_terms_dataframe_with_uris_list.append(dataframe_with_uris)

        print(f"Finished parsing dataframe {filename} to graph!")
    new_terms_dataframe_with_uris = pd.concat(new_terms_dataframe_with_uris_list, ignore_index=True)

    dataframe_with_uris_total = pd.concat([new_terms_dataframe_with_uris, single_source_dataframe_with_uris], ignore_index=True)

    if "results_filenames" in inputs:
        result_dataframe_with_uris_filename = inputs["results_filenames"]["dataframe_with_uris"]
        result_graph_filename = inputs["results_filenames"]["graph"]
    else:
        result_dataframe_with_uris_filename = inputs["dataframe_with_uri"]["filename"]
        result_graph_filename = inputs["graph"]["filename"]

    # store the new dataframe with uris
    result_dataframe_with_uris_filepath = '../dataframe_with_uris/' + result_dataframe_with_uris_filename
    print(f"Saving dataframe with uris to {result_dataframe_with_uris_filepath} ....")
    dataframe_with_uris_total.to_json(result_dataframe_with_uris_filepath, orient="index")
    print("Finished saving dataframe!")

    print("Linking reference terms.....")
    link_reference_terms(new_terms_dataframe_with_uris, graph, single_source_dataframe_with_uris)
    print("Finished linking reference terms!")

    # Save the Graph in the RDF Turtle format
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

