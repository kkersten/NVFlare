# Federated Linear Model with Scikit-learn

## Introduction to Scikit-learn, tabular data, and federated SVM
### Scikit-learn
This example shows how to use [NVIDIA FLARE](https://nvflare.readthedocs.io/en/main/index.html) on tubular data.
It uses [Scikit-learn](https://scikit-learn.org/),
which is a widely used open source machine learning library that supports supervised and unsupervised learning.
### Tabular data
The data used in this example is tabular in a format that can be handled by [pandas](https://pandas.pydata.org/), such that:
- rows correspond to data samples
- first column represents the label 
- the other columns cover the features.    

Each client is expected to have 1 local data file containing both training and validation samples. To load the data for each client, the following parameters are expected by local learner:
- data_file_path: string, full path to the client's data file 
- train_start: int, start row index for training set
- train_end: int, end row index for training set
- valid_start: int, start row index for validation set
- valid_end: int, end row index for validation set

### Federated Linear Model
The machine learning algorithm shown in this example is [Linear classifiers with SGD training](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.SGDClassifier.html).
Under this setting, federated learning can be formulated as a FedAvg process with local training that each client optimizes the local model starting from global parameters with SGD. This can be achieved by setting the `warm_start` flag of SGDClassifier to `True`.

## Data preparation 
The examples illustrate a binary classification task based on [HIGGS dataset](https://archive.ics.uci.edu/ml/datasets/HIGGS).
This dataset contains 11 million instances, each with 28 attributes. Download the dataset from the HIGGS link above, which is a single `.csv` file.
By default, we assume the dataset is downloaded, uncompressed, and stored in `~/dataset/HIGGS.csv`. Note that this `data_path` will be needed in client config `config_fed_client.json`, users can either change it in the config generation script of `prepare_job_config.sh`, or the config json directly.

## (Optional) Set up a virtual environment
```
python3 -m pip install --user --upgrade pip
python3 -m pip install --user virtualenv
```
(If needed) make all shell scripts executable using
```
find . -name ".sh" -exec chmod +x {} \;
```
initialize virtual environment.
```
source ./virtualenv/set_env.sh
```
install required packages for training
```
pip3 install --upgrade pip
pip3 install -r ./virtualenv/requirements.txt
```

## Prepare clients' configs with proper data information 
For realworld FL applications, the config json files are expected to be specified by each client individually, according to their own local data path and splits for training and validation.

In this simulated study, in order to efficiently generate the config files for a study under a particular setting, we provide a script to automate the process, note that manual copying and content modification can achieve the same.

For an experiment with `K` clients, we split one dataset into `K+1` parts in a non-overlapping fashion: `K` clients' training data, and `1` common validation data. To simulate data imbalance among clients, we provided several options for client data splits by specifying how a client's data amount correlates with its ID number (from `1` to `K`):
- Uniform
- Linear
- Square
- Exponential

These options can be used to simulate no data imbalance (uniform), moderate data imbalance (linear), and high data imbalance (square for larger client number e.g. `K=20`, exponential for smaller client number e.g. `K=5` as it will be too aggressive for larger client numbers)

This step is performed by 
```commandline
bash prepare_job_config.sh
```
In this example, we perform experiment with 3 clients under uniform data split. 

Below is a sample config for site-1, saved to `/job_configs/sklearn_linear_5_uniform/app_site-1/config/config_fed_client.json`:
```json
{
    "format_version": 2,
    "executors": [
        {
            "tasks": [
                "train"
            ],
            "executor": {
                "id": "Executor",
                "path": "nvflare.app_opt.sklearn.sklearn_executor.SKLearnExecutor",
                "args": {
                    "learner_id": "linear_learner"
                }
            }
        }
    ],
    "task_result_filters": [],
    "task_data_filters": [],
    "components": [
        {
            "id": "linear_learner",
            "path": "linear_learner.LinearLearner",
            "args": {
                "data_path": "~/dataset/HIGGS.csv",
                "train_start": 1100000,
                "train_end": 3080000,
                "valid_start": 0,
                "valid_end": 1100000,
                "random_state": 0
            }
        }
    ]
}
```

## Run experiment with FL simulator
FL simulator is used to simulate FL experiments or debug codes, not for real FL deployment.
We can run the FL simulator with 3 clients under uniform data split with
```commandline
bash run_experiment_simulator.sh
```
Note that there will be a warning during training: `ConvergenceWarning: Maximum number of iteration reached before convergence. Consider increasing max_iter to improve the fit.`, which is the expected behavior since every round we perform 1-step training on each client. 

Running with deterministic setting `random_state=0`, the resulting curve for `homogeneity_score` is
![linear curve](./figs/linear.png)
