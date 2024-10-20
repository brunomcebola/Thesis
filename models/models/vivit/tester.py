"""
This file contains the Trainer class for the kinetics model
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
# pylint: disable=cell-var-from-loop
# pylint: disable=line-too-long

import math
import torch
import numpy as np
import tensorflow as tf

from transformers import VivitModel

from . import vivit_logits

from ..utils import Tester as _Tester

class Tester(_Tester):
    """
    Tester class for the kinetics model
    """

    def _gen_model(self, checkpoint):
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        pre_logits_model = VivitModel.from_pretrained("google/vivit-b-16x2-kinetics400").to(device) # type: ignore

        logits_model = vivit_logits.ViViTLogits(num_classes=self._num_classes)
        tf.train.Checkpoint(model=logits_model).restore(checkpoint).expect_partial()

        def model(sample):
            """
            Load the model and make predictions
            """

            input = {"pixel_values": torch.tensor(sample).to(device).float()}

            with torch.no_grad():
                outputs = pre_logits_model(**input).last_hidden_state.cpu().numpy()

            return logits_model(outputs)

        return model

    def _gen_sub_samples(self, sample: tf.Tensor) -> list[tf.Tensor]:
        """
        Sub-sample the video into smaller clips of 224 frames
        """
        transposed = False
        if sample.shape[3] > sample.shape[4]:  # type: ignore
            sample = np.transpose(sample, (0, 1, 2, 4, 3))
            transposed = True


        # Apply horizontal sliding window to create sub samples of 224x224
        sub_samples = []
        final = sample.shape[4] - 224 + 1  # type: ignore
        step = int((sample.shape[4] - 224) / math.floor(sample.shape[4] / 224)) - 1  # type: ignore
        for i in range(0, final, step if step > 0 else 1):
            sub_samples.append(sample[:, :, :, :, i : i + 224])  # type: ignore

        # Transpose the sub samples back
        if transposed:
            for i, sample in enumerate(sub_samples):
                sub_samples[i] = np.transpose(sample, (0, 1, 2, 4, 3))

        return sub_samples