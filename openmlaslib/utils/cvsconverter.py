"""
generate_scenario.py -- reads performance data and features from a csv files and generates a simple ASlib scenario
Assumption: features with -512 (missing value) indicate a timeout during feature computation
@author: Marius Lindauer
"""

import arff
import yaml
import copy
from openml.study import get_study
from openml.evaluations import list_evaluations

features = ["ClassEntropy", "DecisionStumpAUC", "DecisionStumpErrRate", "DecisionStumpKappa", "DefaultAccuracy", "Dimensionality", "EquivalentNumberOfAtts", "HoeffdingAdwin.changes", "HoeffdingAdwin.warnings", "HoeffdingDDM.changes", "HoeffdingDDM.warnings", "J48.00001.AUC", "J48.00001.ErrRate", "J48.00001.Kappa", "J48.0001.AUC", "J48.0001.ErrRate", "J48.0001.Kappa", "J48.001.AUC", "J48.001.ErrRate", "J48.001.Kappa", "MajorityClassPercentage", "MajorityClassSize", "MaxAttributeEntropy", "MaxKurtosisOfNumericAtts", "MaxMeansOfNumericAtts", "MaxMutualInformation", "MaxNominalAttDistinctValues", "MaxSkewnessOfNumericAtts", "MaxStdDevOfNumericAtts", "MeanAttributeEntropy", "MeanKurtosisOfNumericAtts", "MeanMeansOfNumericAtts", "MeanMutualInformation", "MeanNominalAttDistinctValues", "MeanSkewnessOfNumericAtts", "MeanStdDevOfNumericAtts", "MinAttributeEntropy", "MinKurtosisOfNumericAtts", "MinMeansOfNumericAtts", "MinMutualInformation", "MinNominalAttDistinctValues", "MinSkewnessOfNumericAtts", "MinStdDevOfNumericAtts", "MinorityClassPerentage", "MinorityClassSize", "NaiveBayesAUC", "NaiveBayesAdwin.changes", "NaiveBayesAdwin.warnings", "NaiveBayesDdm.changes", "NaiveBayesDdm.warnings", "NaiveBayesErrRate", "NaiveBayesKappa", "NoiseToSignalRatio", "NumberOfBinaryFeatures", "NumberOfClasses", "NumberOfFeatures", "NumberOfInstances", "NumberOfInstancesWithMissingValues", "NumberOfMissingValues", "NumberOfNumericFeatures", "NumberOfSymbolicFeatures", "PercentageOfBinaryFeatures", "PercentageOfInstancesWithMissingValues", "PercentageOfMissingValues", "PercentageOfNumericFeatures", "PercentageOfSymbolicFeatures", "Quartile1AttributeEntropy", "Quartile1KurtosisOfNumericAtts", "Quartile1MeansOfNumericAtts", "Quartile1MutualInformation", "Quartile1SkewnessOfNumericAtts", "Quartile1StdDevOfNumericAtts", "Quartile2AttributeEntropy", "Quartile2KurtosisOfNumericAtts", "Quartile2MeansOfNumericAtts", "Quartile2MutualInformation", "Quartile2SkewnessOfNumericAtts", "Quartile2StdDevOfNumericAtts", "Quartile3AttributeEntropy", "Quartile3KurtosisOfNumericAtts", "Quartile3MeansOfNumericAtts", "Quartile3MutualInformation", "Quartile3SkewnessOfNumericAtts", "Quartile3StdDevOfNumericAtts", "REPTreeDepth1AUC", "REPTreeDepth1ErrRate", "REPTreeDepth1Kappa", "REPTreeDepth2AUC", "REPTreeDepth2ErrRate", "REPTreeDepth2Kappa", "REPTreeDepth3AUC", "REPTreeDepth3ErrRate", "REPTreeDepth3Kappa", "RandomTreeDepth1AUC", "RandomTreeDepth1ErrRate", "RandomTreeDepth1Kappa", "RandomTreeDepth2AUC", "RandomTreeDepth2ErrRate", "RandomTreeDepth2Kappa", "RandomTreeDepth3AUC", "RandomTreeDepth3ErrRate", "RandomTreeDepth3Kappa", "StdvNominalAttDistinctValues", "kNN1NAUC", "kNN1NErrRate", "kNN1NKappa"]

def generate_scenario(study_id, measure):
    """ generates an ASlib scenario"""

    study = get_study(study_id)
    evaluations = list_evaluations("predictive_accuracy", setup=study.setups, task=study.tasks)

    setup_flowname = {}
    setup_scenarioname = {}
    task_setup_result = {}
    tasks = set()
    setups = set()
    for idx in range(len(evaluations)):
        task_id = evaluations[idx].task_id
        setup_id = evaluations[idx].setup_id
        flowname = evaluations[idx].flow_name
        value = evaluations[idx][value]

        setup_flowname[setup_id] = flowname
        setup_scenarioname[setup_id] = "%s_%s" %(setup_id,flowname)
        tasks.add(task_id)
        setups.add(setup_id)

        if task_id not in task_setup_result:
            task_setup_result[task_id] = {}
        task_setup_result[task_id][setup_id] = value
    algos = [setup_scenarioname[setup_id] for setup_id in setup_scenarioname.keys()]

    description = {"scenario_id": "OpenML_study_%d" %study_id,
                   "performance_measures": ["runtime"],
                   "maximize": [True],
                   "performance_type": [measure],
                   "algorithm_cutoff_time": 0,
                   "algorithm_cutoff_memory": "?",
                   "features_cutoff_time": "?",
                   "features_cutoff_memory": "?",
                   "algorithms_deterministic": algos,
                   "algorithms_stochastic": "",
                   "features_deterministic": "?",  # TODO
                   "features_stochastic": "",
                   "number_of_feature_steps": 1,
                   "feature_steps": {"ALL": {"provides": "?"}},  # TODO
                   "default_steps": ["ALL"]}

    run_attributes = [["instance_id", "STRING"],
                      ["repetition", "NUMERIC"],
                      ["algorithm", "STRING"],
                      [measure, "NUMERIC"],
                      ["runstatus", ["ok", "timeout", "memout", "not_applicable", "crash", "other"]]
                     ]

    run_data = []
    for task_id in tasks:
        for setup_id in setups:
            if setup_id in task_setup_result[task_id]:
                perf = task_setup_result[task_id][setup_id]
                status = "ok"
            else:
                perf = 0
                status = "other"
            run_data.append([task_id, "1", setup_scenarioname[setup_id], perf, status])

    run_arff = {"attributes": run_attributes,
                "data": run_data,
                "relation": "ALGORITHM_RUNS"
                }
    with open("algorithm_runs.arff", "w") as fp:
        arff.dump(run_arff, fp)

    instances = []
    status = {}
    with open(features_fn, "r") as fp:
        feats = fp.readline().replace("\n", "").split(",")[1:]
        description["features_deterministic"] = copy.deepcopy(feats)
        description["feature_steps"]["ALL"]["provides"] = feats

        attributes = [["instance_id", "STRING"],
                      ["repetition", "NUMERIC"]]
        data = []

        for f in feats:
            attributes.append([f, "NUMERIC"])

        for line in fp:
            line = line.replace("\n", "").split(",")
            inst = line[0]
            feats = line[1:]
            if sum(map(float, feats)) == -512 * len(feats):
                status[inst] = "timeout"
                feats = ["?"] * len(feats)
            else:
                status[inst] = "ok"
            d = [inst, 1]
            d.extend(feats)
            data.append(d)

    fv_data = {"attributes": attributes,
               "data": data,
               "relation": "FEATURES"
               }
    with open("feature_values.arff", "w") as fp:
        arff.dump(fv_data, fp)

    fs_data = [[inst, "1", stat] for inst, stat in status.iteritems()]
    fs_attributes = [
        ["instance_id", "STRING"],
        ["repetition", "NUMERIC"],
        ["ALL", ["ok", "timeout", "memout", "not_applicable", "crash", "other"]]
    ]

    fs_data = {"attributes": fs_attributes,
               "data": fs_data,
               "relation": "FEATURES_RUNSTATUS"
               }

    with open("feature_runstatus.arff", "w") as fp:
        arff.dump(fs_data, fp)

    with open("description.txt", "w") as fp:
        yaml.dump(description, fp, default_flow_style=False)

