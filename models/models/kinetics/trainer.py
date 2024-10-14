"""
This file contains the Trainer class for the kinetics model
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
# pylint: disable=cell-var-from-loop
# pylint: disable=line-too-long

import os
import math
import numpy as np
import tensorflow as tf

from . import i3d
from . import i3d_logits

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

        mixed_5c_model = i3d.InceptionI3d(self._num_classes, final_endpoint="Mixed_5c")
        tf.train.Checkpoint(model=mixed_5c_model).restore(self._input_checkpoint).expect_partial()

        self._mixed_5c_model = mixed_5c_model

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

        sample = tf.convert_to_tensor(np.load(sample), dtype=np.float32)  # type: ignore

        # Transpose the sample if needed to apply horizontal sliding window
        transposed = False
        if sample.shape[2] > sample.shape[3]:  # type: ignore
            sample = tf.transpose(sample, (0, 1, 3, 2, 4))
            transposed = True

        sub_samples = []

        # Apply horizontal sliding window to create sub samples of 224x224
        final = sample.shape[3] - 224 + 1  # type: ignore
        step = int((sample.shape[3] - 224) / math.floor(sample.shape[3] / 224)) - 1  # type: ignore
        for i in range(0, final, step if step > 0 else 1):
            sub_samples.append(sample[:, :, :, i : i + 224, :])  # type: ignore

        # Transpose the sub samples back
        if transposed:
            for i, sample in enumerate(sub_samples):
                sub_samples[i] = tf.transpose(sample, (0, 1, 3, 2, 4))

        # Predict the sub samples
        sub_samples_mixed_5c = []
        for i, sub_sample in enumerate(sub_samples):
            out, _ = self._mixed_5c_model(sub_sample)

            if out.numpy().shape[1] <= 1:
                continue

            sub_samples_mixed_5c.append(out.numpy())

        return sub_samples_mixed_5c

    def _gen_model(self):
        return i3d_logits.InceptionI3dLogits(self._num_classes)

    def _gen_optimizer(self):
        return tf.optimizers.Adam(learning_rate=0.001)

    def _gen_loss(self):
        return tf.losses.SparseCategoricalCrossentropy(from_logits=True)

    def _gen_score(self):

        classes = {i: self._labels.count(i) for i in range(self._num_classes)}
        betas = {0: 2, 1: 2, 2: 0.5, 3: 0.5}

        return CustomFScore(classes=classes, betas=betas)

    def _save_model(self) -> None:
        """
        Save the model
        """

        if self._best_model is None:
            return

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
        self._best_model(logits_sample)
        model_variables = {var.name: var for var in self._best_model.trainable_variables}

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
