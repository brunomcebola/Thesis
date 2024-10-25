"""
This file contains the Trainer class for the HMM model
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
# pylint: disable=cell-var-from-loop
# pylint: disable=line-too-long

import os
import joblib
import logging
import warnings
import numpy as np
from hmmlearn import hmm
from sklearn.model_selection import ParameterGrid

from tqdm import tqdm
from ..utils import Trainer as _Trainer

logging.basicConfig(level=logging.ERROR)
warnings.filterwarnings("ignore")


class Trainer(_Trainer):
    """
    Trainer interface
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._models = {}

    def search(self) -> None:
        samples_class_map = {cls: [] for cls in self._classes}
        best_combinations = {
            cls: {"n_components": 0, "n_iter": 0, "score": float("-inf")} for cls in self._classes
        }

        for sample in self._samples:
            samples_class_map[sample.replace(self._train_data_dir, "").split("/")[1]].append(sample)

        # Example parameter grid
        param_grid = {"n_components": [2, 3, 5, 10], "n_iter": [50, 100, 200, 500]}

        num_combos = len(ParameterGrid(param_grid))

        print(
            f"Performing grid search on {num_combos} hyperparameter combinations with {len(self._samples)} samples"
        )

        for params in ParameterGrid(param_grid):
            for class_name in tqdm(
                self._classes, desc=f"Testing ({params['n_components']}, {params['n_iter']})"
            ):
                feature_files = samples_class_map[class_name]

                all_features = []

                for feature_file in feature_files:
                    features = np.load(feature_file)
                    features = np.squeeze(features, axis=0)
                    features = features[:, ::10, ::10, :]
                    features = features.reshape(features.shape[0], -1)
                    all_features.append(features)

                all_features = np.vstack(all_features)

                model = hmm.GaussianHMM(
                    n_components=params["n_components"],
                    n_iter=params["n_iter"],
                    covariance_type="diag",
                    verbose=False,
                )

                model.fit(all_features)

                try:
                    score = model.score(all_features)
                except Exception:  # pylint: disable=broad-except
                    score = float("-inf")

                if score > best_combinations[class_name]["score"]:
                    best_combinations[class_name]["n_components"] = params["n_components"]
                    best_combinations[class_name]["n_iter"] = params["n_iter"]
                    best_combinations[class_name]["score"] = score
                    self._models[class_name] = model

        print("Best hyperparameters:")
        for class_name, params in best_combinations.items():
            print(f"{class_name}: {params}")

    def train(self):
        pass

    def save(self):
        for cls, model in self._models.items():
            joblib.dump(model, os.path.join(self._output_checkpoint_dir, f"{cls}.pkl"))

    #
    # Abstract methods
    #

    def _get_source_samples(self) -> list:
        _, stream = os.path.basename(self._input_checkpoint_dir).split(".")

        source_samples = []
        for dirpath, _, filenames in os.walk(self._source_data_dir):
            if filenames:
                for f in filenames:
                    if stream in f:
                        source_samples.append(os.path.join(dirpath, f))

        return source_samples

    def _process_source_sample(self, sample: str) -> list:
        return [np.load(sample)]

    def _gen_model(self):
        pass

    def _gen_score(self, confidence_threshold: float):
        pass

    def _save_model(self):
        pass
