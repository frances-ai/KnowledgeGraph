import argparse
import json
from .utils import load_name_map, save_name_map, name_to_uri_name
from .constructions import single_source_eb_dataframe_to_rdf, multiple_source_eb_dataframe_to_rdf, \
    neuspell_corrected_eb_dataframe_to_rdf, add_page_permanent_url, nls_dataframe_to_rdf, merge_graphs
from .enrichments import summary, save_embedding, term_record_linkage, wikidata_linkage, \
    sentiment_analysis, dbpedia_linkage


task_executors = {
    "single_source_eb_dataframe_to_rdf": single_source_eb_dataframe_to_rdf.run_task,
    "multiple_source_eb_dataframe_to_rdf": multiple_source_eb_dataframe_to_rdf.run_task,
    "nls_dataframe_to_rdf": nls_dataframe_to_rdf.run_task,
    "neuspell_corrected_eb_dataframe_to_rdf": neuspell_corrected_eb_dataframe_to_rdf.run_task,
    "add_page_permanent_url": add_page_permanent_url.run_task,
    "merge_graphs": merge_graphs.run_task,
    "summary": summary.run_task,
    "save_embedding": save_embedding.run_task,
    "term_record_linkage":term_record_linkage.run_task,
    "wikidata_linkage": wikidata_linkage.run_task,
    "sentiment_analysis": sentiment_analysis.run_task,
    "dbpedia_linkage":dbpedia_linkage.run_task
}


def get_task_executor(task_name):
    if task_name in task_executors.keys():
        return task_executors[task_name]
    else:
        return None


def read_config(config_file_name):
    config = json.load(open(config_file_name))
    return config


def create_arg_parser():  # pragma: no cover
    parser = argparse.ArgumentParser(
        description='Run knowledge graph generation tasks')
    parser.add_argument('--config_file', help='name of config file', required=True)
    return parser


def parse_common_args():  # pragma: no cover
    parser = create_arg_parser()
    return parser.parse_known_args()


def run_tasks(config):
    tasks = config["tasks"]

    previous_outputs = None

    for task in tasks:
        task_name = task["task_name"]
        if "inputs" not in task:
            inputs = previous_outputs
        else:
            inputs = task["inputs"]
            if previous_outputs:
                inputs.update(previous_outputs)
        task_executor = get_task_executor(task_name)
        outputs = task_executor(inputs)
        previous_outputs = outputs


if __name__ == "__main__":
    name_map_file = "/Users/ly40/Documents/PhD/KnowledgeGraph/GraphGenerator/name_map.pickle"
    load_name_map(name_map_file)
    args, remaining = parse_common_args()
    config = read_config(args.config_file)
    run_tasks(config)
    save_name_map(name_map_file)
