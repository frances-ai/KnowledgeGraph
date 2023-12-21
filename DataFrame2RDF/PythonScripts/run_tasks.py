import argparse
import json
import single_source_eb_dataframe_to_rdf, chapbook_dataframe_to_rdf, multiple_source_eb_dataframe_to_rdf, \
    merge_graphs, summary, similar_terms


task_executors = {
    "single_source_eb_dataframe_to_rdf": single_source_eb_dataframe_to_rdf.run_task,
    "multiple_source_eb_dataframe_to_rdf": multiple_source_eb_dataframe_to_rdf.run_task,
    "chapbook_dataframe_to_rdf": chapbook_dataframe_to_rdf.run_task,
    "merge_graphs": merge_graphs.run_task,
    "summary": summary.run_task,
    "similar_terms": similar_terms.run_task
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
    args, remaining = parse_common_args()
    config = read_config(args.config_file)
    run_tasks(config)
