# 🗺️ GeoSPARQL Fuseki Server Deployment

This repository provides a pre-configured setup to run a GeoSPARQL-enabled Apache Fuseki server using Docker Compose. It supports spatial reasoning via GeoSPARQL and can be used to serve and query RDF knowledge graphs enriched with geospatial data.

## 📁 Folder Structure

```.
├── docker-compose.yml       # Docker Compose setup for GeoSPARQL Fuseki
├── helpers/                 # Contains scripts and tools (e.g. tdbloader) for loading data
└── kgs/                     # RDF Turtle (.ttl) files to be mounted for ingestion
```

⚙️ Prerequisites

* [Docker](https://www.docker.com/)
* [Docker Compose](https://docs.docker.com/compose/install/)
* Download all required KGs from [this link](https://uoe-my.sharepoint.com/:f:/g/personal/s2047051_ed_ac_uk/EuFtKRw-YI1BnDeaGtrl4x8BLcnJEsvLRKJWckzrs2QVDg?email=a.krause%40epcc.ed.ac.uk&e=n7OtEM) (for frances)


## 🚀 Deployment Steps

1. **Clone this repository**

    ```shell
    git clone https://github.com/frances-ai/KnowledgeGraph.git
    cd KnowledgeGraph/fuseki
    ```
2. **Add your RDF data**

   * Place all your .ttl or other RDF files inside the `kgs/` directory.
   * For easy deployment, only add initial RDF files for datasets needed to be persisted. For example, add `hto_eb.ttl` in `kgs/` for 
   the dataset `hto` (used for frances).  

3. **Start the Fuseki server**

    ```shell
    sudo docker-compose up -d
    ```
    * This will start the GeoSPARQL-enabled Fuseki server at http://localhost:3030
      * Default admin password is: pass123

4. **Create the persistent (TDB2) dataset `hto` with initial data loading**

    In sure you have at least 15 RAM memory for the sever, also enough disk storage
    ```shell
    sudo docker exec -it fuseki sh
    # In the container, run
    sh helpers/tdbloader2 --loc databases/hto ../staging/hto_eb.ttl
    ```
    This process could take a while to finish. If it gets stuck or the process get killed, consider increase storage assigned for docker, or remove unused data in docker.

    After it is done, navigate to http://localhost:3030 in your browser, login using the admin password.

    Go to `manage` -> `new dataset` -> enter dataset name `hto` -> select Persist (TDB2) -> click `create dataset`

    Verify the created dataset: go to `datasets` -> click `query` for dataset `hto` -> run the following query:
    ```sparql
    PREFIX hto: <https://w3id.org/hto#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT * WHERE {
      ?article a hto:ArticleTermRecord.
    } LIMIT 10
   ```
   This query should return 10 articles uris if everything works.

5. **Upload the rest of KGs for dataset `hto`**
    In the Fuseki UI, go to `datasets` -> click `add data` for 'hto' dataset -> select downloaded KGs files and upload.

