"""
This file contains the Trainer class for the kinetics model
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
# pylint: disable=cell-var-from-loop
# pylint: disable=line-too-long

import os
import gc
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

        # Create sample tensors
        channels = 3 if "rgb" in os.path.basename(self._input_checkpoint_dir) else 2
        input_sample = tf.convert_to_tensor(np.random.rand(1, 2, 224, 224, channels), dtype=tf.float32)  # type: ignore
        logits_sample = tf.convert_to_tensor(np.random.rand(1, 2, 7, 7, 1024), dtype=tf.float32)  # type: ignore

        # Create a new checkpoint with only the mixed_5c layer
        tf.train.Checkpoint(model=self._mixed_5c_model).write(
            os.path.join(self._tmp_dir, "mixed_5c", "model.ckpt")
        )

        # Restore the full model from the mixed_5c checkpoint
        full_model = i3d.InceptionI3d(num_classes=self._num_classes, final_endpoint="Logits")
        tf.train.Checkpoint(model=full_model).restore(
            os.path.join(self._tmp_dir, "mixed_5c", "model.ckpt")
        ).expect_partial()
        full_model(input_sample)

        # Update the full model with the finetuned logits
        self._model(logits_sample)
        model_variables = {var.name: var for var in self._model.trainable_variables}

        variables_to_replace_map = {
            "inception_i3d/Logits/Conv3d_0c_1x1/conv_3d/b:0": "inception_i3d_logits/Logits/Conv3d_0c_1x1/conv_3d/b:0",
            "inception_i3d/Logits/Conv3d_0c_1x1/conv_3d/w:0": "inception_i3d_logits/Logits/Conv3d_0c_1x1/conv_3d/w:0",
        }

        for i, var in enumerate(full_model.trainable_variables):
            if var.name in variables_to_replace_map:  # type: ignore
                full_model.trainable_variables[i].assign(  # type: ignore
                    model_variables[variables_to_replace_map[var.name]]  # type: ignore
                )

        tf.train.Checkpoint(model=full_model).write(
            os.path.join(self._output_checkpoint_dir, "model.ckpt")
        )
