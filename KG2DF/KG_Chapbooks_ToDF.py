import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Namespace

hto = Namespace("https://w3id.org/hto#")

sparql = SPARQLWrapper(
    "http://35.223.51.36:3030/hot_chapbooks_nls/sparql"
)
sparql.setReturnFormat(JSON)


def create__dataframe():
    info_list = []
    # year, edition num, volume num, start page, end page, term type, name, alter_names [], hq - description, description uri, related terms [{uri: , name: },{}], supplement edition num
    sparql.setQuery("""
    PREFIX hto: <https://w3id.org/hto#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT * WHERE {
        ?page_uri a hto:Page;
            hto:number ?page_num;
            hto:hasOriginalDescription ?desc.
        ?desc hto:text ?text;
            hto:hasTextQuality ?textQuality.
        FILTER NOT EXISTS {
              ?page_uri hto:hasOriginalDescription [hto:hasTextQuality [hto:isTextQualityHigherThan ?textQuality]].
            }
        ?vol a hto:Volume;
            hto:hadMember ?page_uri;
            hto:number ?vol_num;
            hto:title ?vol_title.
        ?series a hto:Series;
            hto:number ?series_num;
            hto:hadMember ?vol;
            hto:genre ?genre.
        OPTIONAL {?series hto:yearPublished ?year_published}
        OPTIONAL {
            ?series hto:printedAt ?printedAt.
            ?printedAt rdfs:label ?print_location.
        }
        }
    """
                    )

    try:
        ret = sparql.queryAndConvert()
        for r in ret["results"]["bindings"]:
            page_uri = r["page_uri"]["value"]
            vol_num = r["vol_num"]["value"]
            year_published = None
            if "year_published" in r:
                year_published = r["year_published"]["value"]
            series_uri = r["series"]["value"]
            description = r['text']["value"]
            series_num = r["series_num"]["value"]
            print_location = None
            if "print_location" in r:
                print_location = r["print_location"]["value"]
            info_list.append({
                "series_uri": series_uri,
                "vol_num": vol_num,
                "vol_title": r["vol_title"]["value"],
                "genre": r["genre"]["value"],
                "print_location": print_location,
                "year_published": year_published,
                "series_num": series_num,
                "page_uri": page_uri,
                "page_num": r["page_num"]["value"],
                "description": description,
                "description_uri": r["desc"]["value"]
            })
    except Exception as e:
        print(e)
    return pd.DataFrame(info_list)


if __name__ == "__main__":
    print("----Getting chapbooks dataframe -----")
    chapbooks_df = create__dataframe()
    result_filename = "chapbooks_kg_nls_dataframe"
    print(f"----Saving the final dataframe to {result_filename}----")
    chapbooks_df.to_json(result_filename, orient="index")

