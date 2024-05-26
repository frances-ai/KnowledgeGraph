# Knowledge Graphs for Textual Heritage

This repository includes code and sources to create knowledge graphs for digitised textual heritage.
Knowledge Graphs generated here are based on the [Heritage Text Ontology](https://w3id.org/hto).
Note that this repository does not introduce any methods to extract information from the source digital datasets whose formats
varies, instead, we utilise the dataframes generated from [Information Extraction for frances Project](https://github.com/frances-ai/frances-InformationExtraction).


## Get Started

#### Step 1: Install required packages (in the root folder):
```commandline
pip install -r requirements.txt
python -m nltk.downloader all
```

#### Step 2: Prepare the source dataframes

Transfer source dataframes (download [here](https://universityofstandrews907-my.sharepoint.com/:f:/g/personal/ly40_st-andrews_ac_uk/Eq9PaN0lcmtHpBdAza8XSOUBmsxok1Zmuyv2R9Y7NnKkoQ?e=ZR64ST)) generated from [Information Extraction for frances Project](https://github.com/frances-ai/frances-InformationExtraction)
to the following folders:

```
.
├── source_dataframes
    ├── chapbooks
        ├── chapbooks_dataframe
    ├── eb
        ├── nls_metadata_dataframe
        ├── final_eb_1_dataframe
        ├── .......
```

#### Step 3: Create Folders

Create folder `results` to store graphs, and `dataframe_with_uris` for temperate dataframe files. The project file 
structure will be:

```
.
├── GraphGenerator
│   ├── dataframe_with_uris
│   ├── configs
│       ├── chapbook_nls_config.json
│       ├── eb_1_hq_config.json
│       ├── ......
│   ├── constructions
│       ├── multiple_source_eb_dataframe_to_rdf.py
│       ├── single_source_eb_dataframe_to_rdf.py
│       ├── ......
│   ├── enrichments
│       ├── summary.py
│       ├── sentiment_analysis.py
│       ├── ......
│   └── PythonScripts
│       ├── run_tasks.py
│       └── utils.py
├── hto.ttl
├── requirements.txt
├── results
└── source_dataframes
```

#### Step 4: Create task configuration json file. 

This file will be passed as an argument when we run the `run_tasks.py`, it will 
tell the program what tasks should execute, what's the inputs and outputs of tasks. So far, we have **implemented 11 tasks executors**:

Construction tasks:
    
1. [single_source_eb_dataframe_to_rdf](GraphGenerator/constructions/single_source_eb_dataframe_to_rdf.py): generates a graph for Encyclopaedia Britannica (EB) using a list of dataframe. Each term in the 
dataframe was extract from single source. For example, this task can deal with the dataframe list with: first edition dataframe extracted from Ash's work, and seven edition from 
National Library of Scotland (NLS). However, it should not be used to process the list with seven edition from NLS, and 
[Knowledge Project ](https://tu-plogan.github.io/source/r_releases.html), because it will ignore all terms in that edition if the edition
has been added to the graph. In this case, it should be handled in the next task `multiple_source_eb_dataframe_to_rdf`.

2. [multiple_source_eb_dataframe_to_rdf](GraphGenerator/constructions/multiple_source_eb_dataframe_to_rdf.py): adds descriptions and extract information of terms in EB extracted from multiple sources.
3. [neuspell_corrected_eb_dataframe_to_rdf](GraphGenerator/constructions/neuspell_corrected_eb_dataframe_to_rdf.py): adds descriptions and extract information of terms in EB corrected using Neuspell.
4. [nls_dataframe_to_rdf](GraphGenerator/constructions/nls_dataframe_to_rdf.py): generates a graph for other NLS collection using a list of dataframe.
5. [add_page_permanent_url](GraphGenerator/constructions/add_page_permanent_url.py): adds page permanent url into the graph. This works for any NLS collection.


Enrichment tasks:
1. [summary](GraphGenerator/enrichments/summary.py): adds summaries of topic terms descriptions to a graph.
2. [save_embedding](GraphGenerator/enrichments/save_embedding.py): generate embeddings for terms with their highest quality descriptions, save the result in a dataframe.
3. [sentiment_analysis](GraphGenerator/enrichments/sentiment_analysis.py): generate binary sentiment labels for terms, save the result in a dataframe.
4. [term_record_linkage](GraphGenerator/enrichments/term_record_linkage.py): links terms across editions by grouping them into concepts, save the result in a dataframe.
5. [wikidata_linkage](GraphGenerator/enrichments/wikidata_linkage.py): Adds Wikidata items to concepts created from [term_record_linkage](GraphGenerator/enrichments/term_record_linkage.py) task.
6. [dbpedia_linkage](GraphGenerator/enrichments/dbpedia_linkage.py): Adds Dbpedia items to concepts created from [term_record_linkage](GraphGenerator/enrichments/term_record_linkage.py) task.

More details of the tasks can be found [here](GraphGenerator/README.md)

The config file below tells the program to first generate a graph for 7th edition EB from the knowledge project, and then 
add summaries to the graph. More examples can be found [here](GraphGenerator/configs)

```json
{
  "tasks": [
    {
      "task_name": "single_source_eb_dataframe_to_rdf",
      "inputs": {
        "dataframes": [
          {"agent": "NCKP",
            "filename":"nckp_final_eb_7_dataframe_clean_Damon"}
        ],
        "results_filenames": {
          "dataframe_with_uris": "nckp_final_eb_7_dataframe_clean_Damon_with_uris",
          "graph": "hto_eb_7th_hq.ttl"
        }
      }
    },
    {
      "task_name": "summary",
      "inputs": {
        "results_filenames": {
          "graph": "hto_eb_7th_hq_summary.ttl"
        }
      }
    }
  ]
}
```

#### Step 5: Run the tasks

In command line, run the python file `run_tasks.py`.
```
python -m GraphGenerator.run_tasks --config_file=<path_to_your_config_file>
# exmaple: python -m GraphGenerator.run_tasks --config_file=GraphGenerator/configs/eb_total_config.json
```

The final graph file can be found `results` folder. 

We have generated some [knowledge graphs](https://universityofstandrews907-my.sharepoint.com/:f:/g/personal/ly40_st-andrews_ac_uk/ElagHP1K_6JJlE9ybROuuVsBsSV8m849oi-a9OPUS5lWFA?e=jJoRuD)


#### Explore the graph using [this notebook](KnowledgeExplorationRemote.ipynb)


