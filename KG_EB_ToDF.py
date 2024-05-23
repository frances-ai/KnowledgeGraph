import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Namespace

hto = Namespace("https://w3id.org/hto#")

sparql = SPARQLWrapper(
    "http://127.0.0.1:3030/hto_eb_total_summary/sparql"
)
sparql.setReturnFormat(JSON)


def create_terms_basic_info_dataframe():
    term_info_list = []
    # year, edition num, volume num, start page, end page, term type, name, alter_names [], hq - description, description uri, related terms [{uri: , name: },{}], supplement edition num
    sparql.setQuery("""
    PREFIX hto: <https://w3id.org/hto#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT * WHERE {
        ?term_uri a ?term_type;
            hto:name ?name;
            hto:startsAtPage ?startPage;
            hto:endsAtPage ?endPage;
            hto:hasOriginalDescription ?desc.
        OPTIONAL {?term_uri hto:note ?note}
        ?desc hto:text ?text;
            hto:hasTextQuality ?textQuality.
        OPTIONAL {
            ?desc hto:hasSummary ?summary_uri.
            ?summary_uri hto:text ?summary.
        }
        FILTER NOT EXISTS {
              ?term_uri hto:hasOriginalDescription [hto:hasTextQuality [hto:isTextQualityHigherThan ?textQuality]].
            }
        FILTER (?term_type = hto:ArticleTermRecord || ?term_type = hto:TopicTermRecord)
        ?startPage hto:number ?s_page_num.
        ?endPage hto:number ?e_page_num.
        ?vol a hto:Volume;
            hto:hadMember ?startPage;
            hto:number ?vol_num;
            hto:title ?vol_title.
        ?edition a hto:Edition;
            hto:hadMember ?vol;
            hto:yearPublished ?year_published;
            hto:genre ?genre;
            hto:printedAt ?printedAt.
        ?printedAt rdfs:label ?print_location.
        OPTIONAL {?edition hto:number ?edition_num}
        }
    """
                    )

    try:
        ret = sparql.queryAndConvert()
        for r in ret["results"]["bindings"]:
            note = None
            if "note" in r:
                note = r["note"]["value"]
            term_uri = r["term_uri"]["value"]
            term_type = "Article" if r["term_type"]["value"] == str(hto.ArticleTermRecord) else "Topic"
            start_page_num = r["s_page_num"]["value"]
            end_page_num = r["e_page_num"]["value"]
            vol_num = r["vol_num"]["value"]
            year_published = r["year_published"]["value"]
            term_name = r["name"]["value"]
            edition_num = None
            edition_uri = r["edition"]["value"]
            description = r['text']["value"]
            summary = None
            if "summary" in r:
                summary = r["summary"]["value"]
            if "edition_num" in r:
                edition_num = r["edition_num"]["value"]
            term_info_list.append({
                "edition_uri": edition_uri,
                "vol_num": vol_num,
                "vol_title": r["vol_title"]["value"],
                "genre": r["genre"]["value"],
                "print_location": r["print_location"]["value"],
                "year_published": year_published,
                "edition_num": edition_num,
                "term_uri": term_uri,
                "note": note,
                "description": description,
                "description_uri": r["desc"]["value"],
                "summary": summary,
                "term_name": term_name,
                "term_type": term_type,
                "start_page_num": start_page_num,
                "end_page_num": end_page_num
            })
    except Exception as e:
        print(e)
    return pd.DataFrame(term_info_list)


def create_reference_terms_dicts():
    sparql.setQuery("""
    PREFIX hto: <https://w3id.org/hto#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT * WHERE {
        ?term_uri a ?term_type;
            hto:refersTo ?reference.
        ?reference hto:name ?name.
        FILTER (?term_type = hto:ArticleTermRecord || ?term_type = hto:TopicTermRecord)
    }
    """
                    )
    ret = sparql.queryAndConvert()
    term_references = {}
    for r in ret["results"]["bindings"]:
        term_uri = r["term_uri"]["value"]
        reference_uri = r["reference"]["value"]
        reference_name = r["name"]["value"]
        reference = {
            "uri": reference_uri,
            "name": reference_name
        }
        if term_uri in term_references:
            term_references[term_uri].append(reference)
        else:
            term_references[term_uri] = [reference]

    return term_references


def create_alter_names_dicts():
    sparql.setQuery("""
    PREFIX hto: <https://w3id.org/hto#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT * WHERE {
        ?term_uri a ?term_type;
            rdfs:label ?alter_name.
        FILTER (?term_type = hto:ArticleTermRecord || ?term_type = hto:TopicTermRecord)
    }
    """
                    )
    ret = sparql.queryAndConvert()
    term_alter_names = {}
    for r in ret["results"]["bindings"]:
        term_uri = r["term_uri"]["value"]
        alter_name = r["alter_name"]["value"]
        if term_uri in term_alter_names:
            term_alter_names[term_uri].append(alter_name)
        else:
            term_alter_names[term_uri] = [alter_name]

    return term_alter_names


def create_supplementing_edition_numbers_dicts():
    sparql.setQuery("""
    PREFIX hto: <https://w3id.org/hto#>
    SELECT * WHERE {
        ?sup a hto:Edition;
            hto:wasSupplementOf ?edition.
        ?edition hto:number ?number.
    }
    """
                    )
    ret = sparql.queryAndConvert()
    supplementing_edition_numbers = {}
    for r in ret["results"]["bindings"]:
        supplement = r["sup"]["value"]
        to = r["number"]["value"]
        if supplement in supplementing_edition_numbers:
            supplementing_edition_numbers[supplement].append(to)
        else:
            supplementing_edition_numbers[supplement] = [to]

    return supplementing_edition_numbers


if __name__ == "__main__":
    print("----Getting terms basic info dataframe -----")
    terms_basic_info_df = create_terms_basic_info_dataframe()
    print("----Getting reference terms -----")
    reference_terms = create_reference_terms_dicts()
    print("----Getting alternative names -----")
    alter_names = create_alter_names_dicts()
    print("----Getting supplementing edition numbers ------")
    supplementing_edition_numbers = create_supplementing_edition_numbers_dicts()

    print("----Adding reference terms, alternative names and supplementing edition numbers to the dataframe ------")
    terms_basic_info_df["alter_names"] = terms_basic_info_df["term_uri"].apply(
        lambda term_uri: alter_names[term_uri] if term_uri in alter_names else [])
    terms_basic_info_df["reference_terms"] = terms_basic_info_df["term_uri"].apply(
        lambda term_uri: reference_terms[term_uri] if term_uri in reference_terms else [])
    terms_basic_info_df["supplements_to"] = terms_basic_info_df["edition_uri"].apply(
        lambda edition_uri: supplementing_edition_numbers[edition_uri] if edition_uri in supplementing_edition_numbers else [])

    result_filename = "eb_kg_hq_dataframe"
    print(f"----Saving the final dataframe to {result_filename}----")
    terms_basic_info_df.to_json(result_filename, orient="index")






