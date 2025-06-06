import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Namespace

hto = Namespace("https://w3id.org/hto#")

sparql = SPARQLWrapper(
    "http://query.frances-ai.com/hto_test/sparql"
)
sparql.setReturnFormat(JSON)


def create_broadsides_basic_info_dataframe():
    broadsides_info_list = []
    # year, edition num, volume num, start page, end page, term type, name, alter_names [], hq - description, description uri, related terms [{uri: , name: },{}], supplement edition num
    sparql.setQuery("""
    PREFIX hto: <https://w3id.org/hto#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT * WHERE {
        ?record_uri a hto:Broadside;
            hto:name ?name;
            hto:number ?num;
            hto:title ?title;
            hto:startsAtPage ?startPage;
            hto:endsAtPage ?endPage;
            hto:hasOriginalDescription ?desc.
        ?desc hto:text ?text;
            hto:hasTextQuality ?textQuality.
        FILTER NOT EXISTS {
              ?record_uri hto:hasOriginalDescription [hto:hasTextQuality [hto:isTextQualityHigherThan ?textQuality]].
            }
        ?startPage hto:number ?s_page_num.
        ?endPage hto:number ?e_page_num.
        ?series a hto:Series;
            hto:hadMember ?record_uri;
            hto:yearPublished ?year_published;
            hto:genre ?genre;
            hto:printedAt ?printedAt.
        ?printedAt rdfs:label ?print_location.
        OPTIONAL {?series hto:number ?series_num}
        }
    """
                    )

    try:
        ret = sparql.queryAndConvert()
        for r in ret["results"]["bindings"]:
            record_uri = r["record_uri"]["value"]
            start_page_num = r["s_page_num"]["value"]
            end_page_num = r["e_page_num"]["value"]
            number = r["num"]["value"]
            year_published = r["year_published"]["value"]
            record_name = r["name"]["value"]
            title = r["title"]["value"]
            series_num = None
            series_uri = r["series"]["value"]
            description = r['text']["value"]
            if "series_num" in r:
                series_num = r["series_num"]["value"]
            broadsides_info_list.append({
                "series_uri": series_uri,
                "vol_num": number,
                "vol_title": title,
                "genre": r["genre"]["value"],
                "print_location": r["print_location"]["value"],
                "year_published": year_published,
                "series_num": series_num,
                "record_uri": record_uri,
                "description": description,
                "description_uri": r["desc"]["value"],
                "name": record_name,
                "start_page_num": start_page_num,
                "end_page_num": end_page_num
            })
    except Exception as e:
        print(e)
    return pd.DataFrame(broadsides_info_list)


if __name__ == "__main__":
    print("----Getting broadsides basic info dataframe -----")
    broadsides_basic_info_df = create_broadsides_basic_info_dataframe()

    result_filename = "broadsides_kg_hq_dataframe"
    print(f"----Saving the final dataframe to {result_filename}----")
    broadsides_basic_info_df.to_json(result_filename, orient="index")






