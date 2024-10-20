"""
This file contains the Trainer class for the kinetics model
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
# pylint: disable=cell-var-from-loop
# pylint: disable=line-too-long

import math
import tensorflow as tf

from . import i3d

from ..utils import Tester as _Tester

class Tester(_Tester):
    """
    Tester class for the kinetics model
    """

    def _gen_model(self, checkpoint):
        model = i3d.InceptionI3d(self._num_classes, final_endpoint="Logits")
        tf.train.Checkpoint(model=model).restore(checkpoint).expect_partial()

        return lambda x: model(tf.convert_to_tensor(x, dtype=tf.float32))

    def _gen_sub_samples(self, sample: tf.Tensor) -> list[tf.Tensor]:
        """
        Sub-sample the video into smaller clips of 224 frames
        """
        sub_samples = []

        transposed = False
        if sample.shape[2] > sample.shape[3]:  # type: ignore
            sample = tf.transpose(sample, (0, 1, 3, 2, 4))
            transposed = True

        final = sample.shape[3] - 224 + 1  # type: ignore
        step = int((sample.shape[3] - 224) / math.floor(sample.shape[3] / 224)) - 1  # type: ignore
        for i in range(0, final, step if step > 0 else 1):
            sub_samples.append(sample[:, :, :, i : i + 224, :])  # type: ignore

        if transposed:
            for i, sample in enumerate(sub_samples):
                sub_samples[i] = tf.transpose(sample, (0, 1, 3, 2, 4))

        return sub_samples