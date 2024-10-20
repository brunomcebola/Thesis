"""
This file contains the Trainer class for the kinetics model
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
# pylint: disable=cell-var-from-loop
# pylint: disable=line-too-long

import os
import math
import torch
import numpy as np
import tensorflow as tf

from transformers import VivitModel
from . import vivit_logits

from ..utils import Trainer as _Trainer
from ..utils import CustomFScore


class Trainer(_Trainer):
    """
    Trainer class for the kinetics model
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize the trainer
        """

        super().__init__(*args, **kwargs)

        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._pre_logits_model = VivitModel.from_pretrained("google/vivit-b-16x2-kinetics400").to(self._device) # type: ignore

    def _get_source_samples(self) -> list:
        source_samples = []
        for dirpath, _, filenames in os.walk(self._source_data_dir):
            if filenames:
                for f in filenames:
                    source_samples.append(os.path.join(dirpath, f))

        return source_samples

    def _process_source_sample(self, sample: str) -> list:
        sample = np.load(sample) # type: ignore

        # Transpose the sample if needed to apply horizontal sliding window
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

        # Predict the sub samples
        sub_samples_pre_logits = []
        for i, sub_sample in enumerate(sub_samples):
            # Run inference with no gradient calculation

            with torch.no_grad():
                out = self._pre_logits_model(**{
                    "pixel_values": torch.tensor(sub_sample).to(self._device).float()
                }).last_hidden_state.cpu().numpy()

            sub_samples_pre_logits.append(out)

            # Free any residual GPU memory
            torch.cuda.empty_cache()

        return sub_samples_pre_logits

    def _gen_model(self):
        return vivit_logits.ViViTLogits(num_classes=self._num_classes)

    def _gen_score(self, confidence_threshold: float):
        # TODO: try not to have this hardcoded
        classes = {i: self._labels.count(i) for i in range(self._num_classes)}
        betas = {0: 2, 1: 2, 2: 0.5, 3: 0.5}
        fallback_label = 2

        return CustomFScore(classes, betas, confidence_threshold, fallback_label)

    def _save_model(self) -> None:
        """
        Save the model
        """

        tf.train.Checkpoint(model=self._model).write(
            os.path.join(self._output_checkpoint_dir, "model.ckpt")
        )


