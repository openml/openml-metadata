"""
Fetches OpenML results for a specific study and evaluation measure and outputs the meta-data as ARFF files
Authors: Jan van Rijn, Joaquin Vanschoren
"""

import arff
import openml
from openml.study import get_study
from openml.evaluations import list_evaluations

def generate_files(study_id, measure):

    # Fetch all its evaluations for a specific study
    print("Fetching evaluation results from OpenML...")
    study = get_study(study_id)
    evaluations = list_evaluations(measure, setup=study.setups, task=study.tasks)

    setup_flowid = {}
    task_data_id = {}
    setup_name = {}
    task_setup_result = {}
    task_qualities = {}
    tasks = set()
    setups = set()

    # obtain the data and book keeping
    for run_id in evaluations.keys():
        task_id = evaluations[run_id].task_id
        flow_id = evaluations[run_id].flow_id
        data_id = evaluations[run_id].data_id
        setup_id = evaluations[run_id].setup_id
        value = evaluations[run_id].value


        task_data_id[task_id] = data_id
        setup_flowid[setup_id] = flow_id
        tasks.add(task_id)
        setups.add(setup_id)

        if task_id not in task_setup_result:
            task_setup_result[task_id] = {}
        task_setup_result[task_id][setup_id] = value

    print("Fetching meta-features from OpenML...")
    # obtain the meta-features
    complete_quality_set = None
    for task_id in tasks:
        qualities = openml.datasets.get_dataset(task_data_id[task_id]).qualities
        task_qualities[task_id] = qualities
        if complete_quality_set is None:
            complete_quality_set = qualities.keys()
        else:
            complete_quality_set = complete_quality_set & qualities.keys()
    complete_quality_set = list(complete_quality_set)

    print("Exporting evaluations...")
    for setup_id in setups:
        flow = openml.flows.get_flow(setup_flowid[setup_id])
        setup_name[setup_id] = "%s_%s" % (setup_id, flow.name)

    run_data = []
    for task_id in tasks:
        for setup_id in setups:
            if setup_id in task_setup_result[task_id]:
                perf = task_setup_result[task_id][setup_id]
                status = "ok"
            else:
                perf = 0
                status = "other"
            run_data.append([task_id, "1", setup_name[setup_id], perf, status])

    run_attributes = [["openml_run_id", "STRING"],
                      ["repetition", "NUMERIC"],
                      ["algorithm", "STRING"],
                      [measure, "NUMERIC"],
                      ["runstatus", ["ok", "timeout", "memout", "not_applicable", "crash", "other"]]
                     ]
    run_arff = {"attributes": run_attributes,
                "data": run_data,
                "relation": "RUN_EVALUATIONS"
                }
    with open("output/runs_evaluations.arff", "w") as fp:
        arff.dump(run_arff, fp)

    print("Exporting meta-features...")
    qualities_attributes = [["openml_data_id", "STRING"],
                            ["repetition", "NUMERIC"]]
    for f in complete_quality_set:
        qualities_attributes.append([f, "NUMERIC"])
    qualities_data = []
    for task_id in tasks:
        current_line = [task_id, "1"]
        for idx, quality in enumerate(complete_quality_set):
            current_value = task_qualities[task_id][quality]
            current_line.append(current_value)
        qualities_data.append(current_line)

    qualities_arff = {"attributes": qualities_attributes,
                      "data": qualities_data,
                      "relation": "FEATURES"
                     }
    with open("output/metafeatures.arff", "w") as fp:
        arff.dump(qualities_arff, fp)
