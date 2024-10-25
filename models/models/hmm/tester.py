"""
This file contains the Trainer class for the kinetics model
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
# pylint: disable=cell-var-from-loop
# pylint: disable=line-too-long

import os
import joblib
import numpy as np

from ..utils import Tester as _Tester


class Tester(_Tester):
    """
    Tester class for the kinetics model
    """

    def _gen_model(self, checkpoint):

        models = {}

        print(os.path.dirname(checkpoint))
        for cls in self._classes:
            models[cls] = joblib.load(os.path.join(os.path.dirname(checkpoint), f"{cls}.pkl"))

        def model(sample):
            log_likelihoods = {}

            features = np.squeeze(sample, axis=0)
            features = features[:, ::10, ::10, :]
            features = features.reshape(features.shape[0], -1)

            # Calculate log likelihoods for the test features
            for class_name, model in models.items():
                log_likelihoods[class_name] = model.score(features)

            # Return as logits array
            return (
                np.expand_dims(
                    np.array([log_likelihoods[class_name] for class_name in self._classes]), axis=0
                ),
                None,
            )

        return model

    def _gen_sub_samples(self, sample: np.ndarray) -> list[np.ndarray]:
        return [sample]
