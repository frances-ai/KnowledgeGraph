# HTO Knowledge Graphs Generator (Deprecated)

This python code is for generating knowledge graphs for digitised textual heritage based on [Heritage Text Ontology](https://w3id.org/hto).
Note that this repository does not introduce any methods to extract information from the source digital datasets whose formats
varies, instead, we utilise the dataframes generated from [Information Extraction for frances Project](https://github.com/frances-ai/frances-InformationExtraction).

----

## How to use this generator

### 1. Set up environment
see the first 3 steps in [Get Started](../../README.md) section.

### 2. Create task configuration json file.

This file will be passed as an argument when we run the `run_tasks.py`, it will 
tell the program what tasks should execute, what's the inputs and outputs of tasks. The format of this is:

```
{
  "tasks*": [
    {
      "task_name*": "task_name_1",
      "inputs*": {
        "dataframes": [
          {"agent": "agent1",
            "filename":"dataframe_1"}
        ],
        "results_filenames*": {
          "dataframe_with_uris": "dataframe_1_with_uris",
          "graph*": "result_graph_1.ttl"
        }
      }
    },
    {
      "task_name*": "task_name_2",
      "inputs": {
        "results_filenames": {
          "graph": "result_graph_1.ttl"
        }
      }
    }
    ....
  ]
}
```

Overall, this JSON file shows a list of tasks, with `task_name` and `inputs`, where `task_name` has should match one of these 
[tasks](#tasks), the format of `inputs` varies from different tasks (will talk a bit more in [Tasks section](#tasks)). 

When you run multiple tasks, please carefully choose the order of each task! Especially when the next task takes the outputs of 
previous task's as inputs.

Note that keys ending with start * means it is required, otherwise, it is optional. For example, the key `tasks` is required. 
`inputs` in the first task is required, while it is often optional in the second task. However, whether it is required is also based on
the specific task. Basically, each task needs `inputs`, but you don't have to include it in each task when writing the JSON file.
When you run multiple tasks, and there is not `inputs` after task1 in the JSON file, then the outputs of previous task will be automatically 
added into the `inputs` of the current task when you run the generator. 

You can find some examples in [configs](configs) folder.

### 3. Run the generator

In command line, navigate to current folder `PythonScripts`, and then run the python file `run_tasks.py` with config JSON file.
```
cd DataFrame2RDF/PythonScripts
python run_tasks.py --config_file=<path_to_your_config_file>
```

This `run_tasks.py` first reads and parses this JSON file into Python object. It gets a list of tasks from JSON file. 
For each task, it gets a task executor based on the task name. This executor is the `run_task(inputs)` function in each task python file.
It takes inputs from the task and return outputs, if it is not the first task, inputs will be updated using previous outputs.   

The final graph file can be found `results` folder.


## Agents

Current this generator supports the source from three agents: National Library of Scotland (short for NLS), Ash Charlton (short for Ash),
[Nineteenth Century Knowledge Project](https://tu-plogan.github.io/source/r_releases.html) (short for NCKP). When writing config
file, please use the short name for these agents.

## Tasks

### 1. single_source_eb_dataframe_to_rdf

inputs:
```json
{
    "dataframes*": [
      {
        "agent*": "agent1",
        "filename*": "eb_dataframe_1"
      },
      ....
    ],
    "results_filenames*": {
      "dataframe_with_uris*": "dataframe_uris",
      "graph*": "result_hto_eb.ttl"
    }
}
```

outputs:
```json
{
    "dataframe_with_uris": {
        "filename": "result_dataframe_with_uris_filename",
        "object": dataframe_with_uris_total
    },
    "graph": {
        "filename": "result_graph_filename",
        "object": result_graph
    }
}
```

This task generates a graph for Encyclopaedia Britannica (EB) using a list of dataframe. **Each term in the 
dataframe was extract from single source.** For example, this task can deal with the dataframe list with: first edition dataframe extracted from Ash's work, and seven edition from 
National Library of Scotland (NLS). However, it should not be used to process the list with seven edition from NLS, and 
[Knowledge Project ](https://tu-plogan.github.io/source/r_releases.html), because it will ignore all terms in that edition if the edition
has been added to the graph. In this case, it should be handled in the next task `multiple_source_eb_dataframe_to_rdf`.
Therefore, it is important to **check the order in the dataframes**, especially when there are overlapping editions in two dataframes.

This task returns two outputs: _dataframe_with_uris_ and _graph_. 
_dataframe_with_uris_ includes all source dataframes with extra column `uri` which is the term uri in the output graph. 
The graph generated by this task will include all EB [Bibliographical Metadata](https://w3id.org/hto#desc-biblio) in HTO, 
and all [Textual Content](https://w3id.org/hto#desc-content) expect grouping terms to concept, adding summaries, linking similar terms 
(these will be done by other tasks).

Note that **One term should have only one reference term** with specific name. If there are more than one terms have such name, 
then in theory, we should only take the term which is talking about the same topic. 
However, some term has no meaningful description except alternative names, or "See Term". In this case, there is no way to identify the topic, 
so for now we always take the first reference term found. In the further, we will evaluate the accuracy and efficiency of the current method to locate specific
reference term, and compare it with different methods, such as checking the topics if the both terms descriptions are meaningful,
otherwise, take the first reference term found.


### 2. multiple_source_eb_dataframe_to_rdf

inputs: 
```json
{
    "dataframes*": [
      {
        "agent*": "agent1",
        "filename*": "eb_dataframe_1"
      },
      ....
    ],
    "dataframe_with_uris*": {
        "filename*": "single_source_dataframe_uris"
    },
    "graph*": {
        "filename": "hto_eb_single_source.ttl"
    },
    "results_filenames": {
      "dataframe_with_uris": "dataframe_uris",
      "graph": "result_hto_eb.ttl"
    }
}
```

outputs:
```json
{
    "dataframe_with_uris": {
        "filename": "result_dataframe_with_uris_filename",
        "object": dataframe_with_uris_total
    },
    "graph": {
        "filename": "result_graph_filename",
        "object": result_graph
    }
}
```

This task adds descriptions and extract information (note, alternative names if exists) of terms in EB extracted from multiple sources
to a single source graph. In the inputs, besides the dataframes, it requires the outputs (single source graph and dataframe_with_uris) of [above task](#1-singlesourceebdataframetordf).
Since this task will not add metadata of edition and volume, source dataframes in the `dataframes` list should only have editions
which has been added to the input graph. Otherwise, use [above task](#1-singlesourceebdataframetordf) instead.
Note that, `results_filenames` is optional in this task. If it is not specified, then it will take the sames as input dataframe_with_uris
and graph. This is designed to reduce the intermediate files and make it easier to write a config file, since when it comes to multiple tasks in one config file,
the outputs of a task can be added to the inputs for next task.

In theory, this task should not add new terms to the graph but only descriptions with different text quality of existing terms, since no new edition is added.
However, different set of terms could be recognized from different sources. For example, some term might be in the description of another term. Or, different term names
might be recognized even though they are theoretically identical. Therefore, it is extremely difficult and expensive to identify same terms.
For now, this task is implemented based on the following assumptions:
1. Same term must have exactly the same name.
2. Multiple terms could have the same name.
3. Terms with same name but not similar description will not be considered as identical.
4. Two descriptions are similar if the first couple of sentences are similar.
5. If term _A_, term _B_ are the only two terms in edition _E_ of the input graph has name _a_, and there is list of terms in source dataframe having the same name _a_ and they
are also in edition _E_. The first term _C_ in that list having the similar description as term _A_ will be considered as the same term
as term _A_. And then term _B_ will not be compared with term _C_.

We designed a method to check similarity of two description using the [SequenceMatcher](https://docs.python.org/3/library/difflib.html).
Overall, it first truncates descriptions which are over the MAX_LENGTH, and then compute the similar score using quick ratio. 
If the score reach threshold, then they are similar. Otherwise, if their lengths are different, then truncate the longer one so that they 
have same length, then compute the score again and compare with threshold.

This task also returns two outputs: _dataframe_with_uris_ and _graph_. 
_dataframe_with_uris_ includes the dataframe of new terms with extra column `uri` for term uri along with the input dataframe_with_uris. 
The graph generated by this task will add extra terms and descriptions from different sources to the input graph. 


### 3. chapbook_dataframe_to_rdf

inputs: 
```json
{
    "dataframes*": [
      {
        "agent*": "agent1",
        "filename*": "chapbook_dataframe_1"
      },
      ....
    ],
    "results_filenames*": {
      "graph*": "result_hto_chapbook.ttl"
    }
}
```

outputs:
```json
{
    "graph": {
        "filename": "result_graph_filename",
        "object": result_graph
    }
}
```

This task generates a graph for Chapbooks using a list of dataframe. It is very similar to [single_source_eb_dataframe_to_rdf](#1-singlesourceebdataframetordf), 
it is also for single source. Unlike EB, it can only get textual content in a page level. 


### 4. merge_graphs

inputs: 

```json
{
    "graphs_filenames*": [
      "hto_chapbooks_nls.ttl",
      "hto_eb_total.ttl"
    ],
    "results_filenames*": {
      "graph*": "hto_total.ttl"
    }
}
```

outputs:

```json
{
    "graph": {
        "filename": result_graph_filename,
        "object": graph
    }
}
```

This task merges graphs for different collections into one graph. `inputs` and `graphs_filenames` have to be included in the 
config files, because it can not be obtained from previous outputs directly. 

### 5. summary 

inputs: 

```json
{
    "graph": {
      "filename": "hto_eb_7th_hq.ttl"
    },
    "results_filenames": {
      "graph": "hto_eb_7th_hq_summary.ttl"
    }
}
```

outputs:
```json
{
    "graph": {
        "filename": "result_graph_filename",
        "object": result_graph
    }
}
```

This task adds summaries of topic terms descriptions to a graph. It first queries all the descriptions of topic terms (it could 
get multiple descriptions of one term). Then summarise each description and add the summary to the graph. 
This task applies extractive summarization method using [bert-extractive-summarizer](https://pypi.org/project/bert-extractive-summarizer/).


### 6. similar_terms

inputs: 
```json
{
    "graph": {
      "filename": "hto_eb_7th_hq_summary.ttl"
    },
    "results_filenames": {
      "graph": "hto_eb_7th_hq_summary_similar.ttl"
    }
}
```

outputs:

```json
{
    "graph": {
        "filename": "result_graph_filename",
        "object": result_graph
    }
}
```

This task links similar terms in the input graph. It first queries all the descriptions with the highest text quality of terms 
(only highest quality description will represent the meaning of the term). Then it computes the similarity score of one description against other descriptions.
For each description, it will take the top 20 similar descriptions with similarity score over the predefined threshold as similar descriptions.  
Meanwhile, it links the terms of these similar descriptions using similarTo property in HTO. This task applies [paraphrase mining](https://www.sbert.net/examples/applications/paraphrase-mining/README.html) to find similar
descriptions.