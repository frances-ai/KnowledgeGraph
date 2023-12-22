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
├── DataFrame2RDF
│   ├── dataframe_with_uris
│   └── PythonScripts
│       ├── configs
│       │   ├── chapbook_nls_config.json
│       │   ├── eb_1_hq_config.json
│       │   ├── ......
│       ├── chapbook_dataframe_to_rdf.py
│       ├── merge_graphs.py
│       ├── multiple_source_eb_dataframe_to_rdf.py
│       ├── run_tasks.py
│       ├── similar_terms.py
│       ├── single_source_eb_dataframe_to_rdf.py
│       ├── summary.py
│       └── utils.py
├── hto.ttl
├── requirements.txt
├── results
└── source_dataframes
```

#### Step 4: Create task configuration json file. 

This file will be passed as an argument when we run the `run_tasks.py`, it will 
tell the program what tasks should execute, what's the inputs and outputs of tasks. So far, we have **implemented 6 tasks executors**:
    
1. [single_source_eb_dataframe_to_rdf](DataFrame2RDF/PythonScripts/single_source_eb_dataframe_to_rdf.py): generates a graph for Encyclopaedia Britannica (EB) using a list of dataframe. Each term in the 
dataframe was extract from single source. For example, this task can deal with the dataframe list with: first edition dataframe extracted from Ash's work, and seven edition from 
National Library of Scotland (NLS). However, it should not be used to process the list with seven edition from NLS, and 
[Knowledge Project ](https://tu-plogan.github.io/source/r_releases.html), because it will ignore all terms in that edition if the edition
has been added to the graph. In this case, it should be handled in the next task `multiple_source_eb_dataframe_to_rdf`.

2. [multiple_source_eb_dataframe_to_rdf](DataFrame2RDF/PythonScripts/multiple_source_eb_dataframe_to_rdf.py): adds descriptions and extract information of terms in EB extracted from multiple sources.
3. [chapbook_dataframe_to_rdf](DataFrame2RDF/PythonScripts/chapbook_dataframe_to_rdf.py): generates a graph for Chapbooks using a list of dataframe.
4. [merge_graphs](DataFrame2RDF/PythonScripts/merge_graphs.py): merges graphs for different collections into one graph.
5. [summary](DataFrame2RDF/PythonScripts/summary.py): adds summaries of topic terms descriptions to a graph.
6. [similar_terms](DataFrame2RDF/PythonScripts/similar_terms.py): linking similar terms in a graph.

More details of the tasks can be found [here](DataFrame2RDF/PythonScripts/README.md)

The config file below tells the program to first generate a graph for 7th edition EB from the knowledge project, and then 
add summaries to the graph. More examples can be found [here](DataFrame2RDF/PythonScripts/configs)

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

In command line, navigate to this folder `DataFrame2RDF/PythonScripts`, and then run the python file `run_tasks.py`.
```
cd DataFrame2RDF/PythonScripts
python run_tasks.py --config_file=<path_to_your_config_file>
```

The final graph file can be found `results` folder.

#### Explore the graph using [this notebook](KnowledgeExploration.ipynb)


