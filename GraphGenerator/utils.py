import pickle
import random

import regex
from rdflib import Literal, XSD, RDF, URIRef
from rdflib.namespace import FOAF, PROV, Namespace
from tqdm import tqdm

import re

NON_AZ09_REGEXP = regex.compile('[^\p{L}\p{N}]')
MAX_SIZE_NAMES = 10000000000

name_map = {}


def get_term_id_from_uri(term_uri):
    return term_uri.split("/")[-1]


def remove_extra_spaces(text):
    text = text.strip()
    # Remove extra spaces before punctuation
    text = re.sub(r'\s+([,.;:])', r'\1', text)
    # Remove extra spaces around slashes and hyphens that are not part of words
    #text = re.sub(r'\s*/\s*', '/', text)
    text = re.sub(r'\s*-\s*', '-', text)
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    return text


def name_to_uri_name(name):
    """
    Convert a name to a format which will be shown in the uri of a resource. This format (uri name) is digits based,
    which means  a sequence of digits are used to represent the name in the uri. Same name should have the
    same uri name.
    :param name: name of a resource
    :return: string as uri name (digits based).
    """
    if name in name_map:
        return name_map[name]

    name_id = random.randint(0, MAX_SIZE_NAMES)
    while str(name_id) in name_map.values():
        name_id = random.randint(0, MAX_SIZE_NAMES)
    name_map[name] = str(name_id)
    return str(name_id)


def save_name_map(filepath):
    """
    Save the name map into a pickle file, so it can be used to convert names to uri names, thus the form of uri
    can be consistent - same name should have the same uri name.
    :param filepath: where the file will be stored.
    :return:
    """
    with open(filepath, 'wb') as f:
        pickle.dump(name_map, f)


def load_name_map(filepath):
    """
    Load the name map from a pickle file, so it can be used to convert names to uri names, thus the form of uri
    can be consistent - same name should have the same uri name.
    :param filepath: where the file will be stored.
    :return:
    """
    try:
        with open(filepath, 'rb') as f:
            global name_map
            name_map = pickle.load(f)
    except FileNotFoundError:
        print("file not found")
        name_map = {}


hto = Namespace("https://w3id.org/hto#")

agents = {
    "NCKP": ["Nineteenth-Century Knowledge Project", hto.Organization, 'https://tu-plogan.github.io'],
    "Ash": ["Ash Charlton", hto.Person, 'https://scholar.google.com/citations?user=-IIqUJ8AAAAJ&hl=en'],
    "NLS": ["National Library of Scotland", hto.Organization, 'https://www.nls.uk']
}


#TODO fix bug: create uri based on their type
def create_organization(agent, graph):
    agent_uri = URIRef("https://w3id.org/hto/Organization/" + agent)
    if (agent_uri, RDF.type, agents[agent][1]) in graph:
        return agent_uri
    graph.add((agent_uri, RDF.type, agents[agent][1]))
    graph.add((agent_uri, FOAF.homepage, URIRef(agents[agent][2])))
    graph.add((agent_uri, FOAF.name, Literal(agents[agent][0], datatype=XSD.string)))
    return agent_uri


def create_dataset(collection_short_name, agent_uri, agent, graph):
    dataset = URIRef("https://w3id.org/hto/Collection/" + agent + "_" + collection_short_name + "_dataset")
    if (dataset, RDF.type, PROV.Collection) in graph:
        return dataset
    graph.add((dataset, RDF.type, PROV.Collection))
    graph.add((dataset, PROV.wasAttributedTo, agent_uri))

    # Create digitalising activity
    digitalising_activity = URIRef("https://w3id.org/hto/Activity/" + agent + "_digitalising_activity")
    graph.add((digitalising_activity, RDF.type, hto.Activity))
    graph.add((digitalising_activity, PROV.generated, dataset))
    graph.add((digitalising_activity, PROV.wasAssociatedWith, agent_uri))
    graph.add((dataset, PROV.wasGeneratedBy, digitalising_activity))
    return dataset


defoe = URIRef("https://github.com/defoe-code/defoe")
frances_information_extraction = URIRef("https://github.com/frances-ai/frances-InformationExtraction")
ABBYYFineReader = URIRef("https://pdf.abbyy.com")

all_software_list = [
    {
        "uri": defoe,
        "name": "defoe"
    },
    {
        "uri": frances_information_extraction,
        "name": "frances information extraction"
    },
    {
        "uri": ABBYYFineReader,
        "name": "ABBYY FineReader"
    }
]


def add_software_with_name(software_list, graph):
    for software in software_list:
        graph.add((software["uri"], RDF.type, hto.SoftwareAgent))
        graph.add((software["uri"], FOAF.name, Literal(software["name"], datatype=XSD.string)))


def add_software(software_list, graph):
    for software in software_list:
        graph.add((software, RDF.type, hto.SoftwareAgent))


def link_entity_with_software(graph, entity, entity_type, agent):
    software = None
    if entity_type == "description":
        if agent == "NLS":
            software = defoe
        else:
            software = frances_information_extraction
    else:
        if agent == "NCKP":
            software = ABBYYFineReader

    if software:
        graph.add((entity, PROV.wasAttributedTo, software))


def get_term_class_name_and_term_ref(term_type, term_id):
    term_ref = URIRef("https://w3id.org/hto/" + term_type + "/" + term_id)
    term_class_name = hto.ArticleTermRecord
    if term_type == "TopicTermRecord":
        term_class_name = hto.TopicTermRecord
    return term_class_name, term_ref


def get_term_class_name(term_type, hto):
    term_class_name = hto.ArticleTermRecord
    if term_type == "TopicTermRecord":
        term_class_name = hto.TopicTermRecord
    return term_class_name


def get_source_ref(filePath, agent):
    if agent == "NCKP":
        parts = filePath.split("/")
        if len(parts) < 3:
            raise Exception("Wrong input format")
        edition_parts = parts[-3].split("_", 1)
        file_uri = "https://raw.githubusercontent.com/TU-plogan/kp-editions/main/" + edition_parts[0] + "/" + \
                   edition_parts[1] + "/" + parts[-2] + "/" + parts[-1]
        source_ref = URIRef(file_uri)
    else:
        source_uri_name = filePath.replace("/", "_").replace(".", "_")
        source_ref = URIRef("https://w3id.org/hto/InformationResource/" + source_uri_name)
    return source_ref


def link_reference_terms(new_terms_dataframe_with_uris, graph, previous_dataframe_with_uris=None):
    """
    Given a dataframe and a graph, return the graph with triples that links a term with its reference terms using refersTo property. the dataframe should have the column called reference_terms, a list of strings representing term names, uris.
    :param new_terms_dataframe_with_uris: dataframe with uris of eb collection from single source, terms in this
    dataframe are added in this specific task
    :param previous_dataframe_with_uris: terms in this dataframe are added in previous task
    :param graph: graph of eb collection from single source, it does not have links for reference terms
    :return: a graph
    """
    # 1. In dataframe, find all term records that have non-empty reference-terms
    # 2. For each term in above records, find the term URI in graph.
    # 3. then find all term URIs in graph that has name which appears in reference-terms
    # 4. create triples with refersTo relation for term uri and reference term uri.
    compare_df = new_terms_dataframe_with_uris
    if not isinstance(previous_dataframe_with_uris, type(None)):
        compare_df = previous_dataframe_with_uris
    df_with_references = new_terms_dataframe_with_uris[new_terms_dataframe_with_uris["reference_terms"].apply(
        lambda references: len(references) > 0 and references[0] != '')].reset_index(drop=True)
    for df_term_index in tqdm(range(0, len(df_with_references)), desc="Processing", unit="item"):
        # find the term URI in graph
        df_term = df_with_references.loc[df_term_index]
        term_uri = URIRef(str(df_term["uri"]))
        edition_mmsid = df_term["MMSID"]
        reference_terms = df_term["reference_terms"]
        for reference_term in reference_terms:
            if reference_term == "":
                continue
            references_df = compare_df[
                (compare_df["MMSID"] == edition_mmsid) & (compare_df["term"] == reference_term)].reset_index(drop=True)
            if len(references_df) > 0:
                # One term should have only one reference term with specific name. If there are more than one terms have such name, then in theory, we should only take the term which is talking about the same topic. However, some term has no meaningful description except alternative names, or "See Term". In this case, there is no way to identify the topic, so we always take the first reference term found.
                refers_to = URIRef(str(references_df.loc[0]["uri"]))
                # print(f"link {term_uri} in {edition_mmsid} to {refers_to}")
                graph.add((term_uri, hto.refersTo, refers_to))
    return graph
