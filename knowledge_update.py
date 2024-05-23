from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper(
    "http://www.frances-ai.com:3030/hto_total_inferred"
)
sparql.setReturnFormat(JSON)

if __name__ == "__main__":
    queryString = """
    PREFIX foaf:  <http://xmlns.com/foaf/0.1/>
    PREFIX hto: <https://w3id.org/hto#>
    DELETE { ?page eb:header ?header }
    INSERT { ?agent foaf:name 'Nineteenth-Century Knowledge Project' }
    WHERE
      { ?agent a hto:Agent;
            foaf:name 'Nineteen Century Knowledge Project'
      }
    """
    sparql.setQuery(queryString)
    sparql.method = 'POST'
    sparql.query()