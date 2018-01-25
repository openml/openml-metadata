"""
Fetches OpenML results for a specific study and evaluation measure and outputs the meta-data as ARFF files
Authors: Jan van Rijn, Joaquin Vanschoren
"""

import arff
import openml
import pandas as pd
from openml.study import get_study
from openml.evaluations import list_evaluations

def list_all(listing_call, *args, **filters):
    """Helper to handle paged listing requests.
    Example usage: evaluations = list_all(list_evaluations, "predictive_accuracy", task=mytask)

    Parameters
    ----------
    listing_call : object
        Name of the listing call, e.g. list_evaluations
    *args : Variable length argument list
        Any required arguments for the listing call
    **filters : Arbitrary keyword arguments
        Any filters that need to be applied

    Returns
    -------
    object
    """
    batch_size = 10000
    page = 0
    has_more = 1
    result = {}
    while has_more:
        new_batch = listing_call(*args, size=batch_size, offset=batch_size*page, **filters)
        result.update(new_batch)
        page += 1
        has_more = (len(new_batch) == batch_size)
    return result


def generate_files(study_id, measure):

    # Fetch all its evaluations for a specific study
    print("Fetching evaluation results from OpenML...")
    study = get_study(study_id)
    evaluations = list_all(list_evaluations, measure, setup=study.setups, task=study.tasks)

    setup_flowid = {}
    task_data_id = {}
    setup_name = {}
    setup_detail = {}
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
        try:
            qualities = openml.datasets.get_dataset(task_data_id[task_id]).qualities
            task_qualities[task_id] = qualities
            if complete_quality_set is None:
                complete_quality_set = qualities.keys()
            else:
                complete_quality_set = complete_quality_set & qualities.keys()
        except arff.BadDataFormat:
            print("Error parsing dataset: "+str(task_data_id[task_id]))
        except arff.BadAttributeType:
            print("Error parsing dataset: "+str(task_data_id[task_id]))
    complete_quality_set = list(complete_quality_set)

    print("Exporting evaluations...")
    for setup_id in setups:
        flow = openml.flows.get_flow(setup_flowid[setup_id])
        setup_name[setup_id] = "%s_%s" % (setup_id, flow.name)
        setup_params = openml.setups.get_setup(setup_id).parameters
        if setup_params:
            setup_detail[setup_id] = ','.join("{}:{}".format(p.parameter_name, p.value) for p in setup_params.values())
        else:
            setup_detail[setup_id] = ''

    run_data = []
    for task_id in tasks:
        for setup_id in setups:
            if setup_id in task_setup_result[task_id]:
                perf = task_setup_result[task_id][setup_id]
                status = "ok"
            else:
                perf = 0
                status = "other"
            run_data.append([task_id, "1", setup_name[setup_id], setup_detail[setup_id]+" ", perf, status])

    run_attributes = [["openml_task_id", "NUMERIC"],
                      ["repetition", "NUMERIC"],
                      ["algorithm", "STRING"],
                      ["hyperparameters", "STRING"],
                      [measure, "NUMERIC"],
                      ["runstatus", ["ok", "timeout", "memout", "not_applicable", "crash", "other"]]
                     ]
    run_arff = {"attributes": run_attributes,
                "data": run_data,
                "relation": "RUN_EVALUATIONS"
                }
    with open("output/study_" + str(study_id) + "_run_evaluations_" + measure + ".arff", "w") as fp:
        arff.dump(run_arff, fp)

    print("Exporting meta-features...")
    qualities_attributes = [["openml_task_id", "NUMERIC"],
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
                      "relation": "METAFEATURES"
                     }
    with open("output/study_" + str(study_id) + "_metafeatures.arff", "w") as fp:
        arff.dump(qualities_arff, fp)

    print("Exporting joint table...")
    eval_labels = ['openml_task_id', 'repetition', 'algorithm', 'hyperparameters', measure, 'runstatus']
    df_evals = pd.DataFrame.from_records(run_data, columns=eval_labels)
    quality_labels = ['openml_task_id', 'repetition']
    quality_labels.extend(complete_quality_set);

    df_qualities = pd.DataFrame.from_records(qualities_data, columns=quality_labels)

    joint_data = pd.merge(df_evals, df_qualities, how='left', on=['openml_task_id','repetition'])

    joint_attributes = run_attributes
    for f in complete_quality_set:
        joint_attributes.append([f, "NUMERIC"])

    joint_arff = {"attributes": joint_attributes,
                  "data": joint_data.values,
                  "relation": "JOINTMETADATA"
                 }

    with open("output/study_" + str(study_id) + "_joint.arff", "w") as fp:
        arff.dump(joint_arff, fp)
