# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Loads a sample video and classifies using a trained Kinetics checkpoint."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import gc
import os
import math
import numpy as np
import tqdm

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf  # pylint: disable=wrong-import-position

import i3d  # pylint: disable=wrong-import-position

_SAMPLES_PATH = "npy/rgb"
_OUTPUT_PATH = "data/rgb"

_CHECKPOINTS_PATH = "checkpoints"


def main():
    """
    Main function to evaluate I3D on Kinetics.
    """

    # Instantiate the model for RGB
    rgb_model = i3d.InceptionI3d(400, spatial_squeeze=True, final_endpoint="Mixed_5c")

    # Restore the checkpoint
    tf.train.Checkpoint(model=rgb_model).restore(
        os.path.join(_CHECKPOINTS_PATH, "rgb", "model.ckpt")
    ).expect_partial()

    # Instantiate the model for flow
    flow_model = i3d.InceptionI3d(400, spatial_squeeze=True, final_endpoint="Mixed_5c")

    # Restore the checkpoint
    tf.train.Checkpoint(model=flow_model).restore(
        os.path.join(_CHECKPOINTS_PATH, "flow", "model.ckpt")
    ).expect_partial()

    for cls in os.listdir(_SAMPLES_PATH):
        print(f"Generating data for: {cls}")

        samples = os.listdir(os.path.join(_SAMPLES_PATH, cls))

        for sample in tqdm.tqdm(samples):

            os.makedirs(os.path.join(_OUTPUT_PATH, cls, sample), exist_ok=True)

            rgb_samples = []

            # RGB
            rgb_sample = tf.convert_to_tensor(
                np.load(os.path.join(_SAMPLES_PATH, cls, sample, f"{sample}_rgb.npy")),
                dtype=tf.float32,
            )

            transposed = False
            if rgb_sample.shape[2] > rgb_sample.shape[3]:  # type: ignore
                rgb_sample = tf.transpose(rgb_sample, (0, 1, 3, 2, 4))
                transposed = True

            rgb_sub_samples = []

            final = rgb_sample.shape[3] - 224 + 1  # type: ignore
            step = int((rgb_sample.shape[3] - 224) / math.floor(rgb_sample.shape[3] / 224)) - 1  # type: ignore # pylint: disable=line-too-long
            for i in range(0, final, step if step > 0 else 1):
                rgb_sub_samples.append(rgb_sample[:, :, :, i : i + 224, :])  # type: ignore

            if transposed:
                for i, sample in enumerate(rgb_sub_samples):
                    rgb_sub_samples[i] = tf.transpose(sample, (0, 1, 3, 2, 4))

            for ssi, sub_sample in enumerate(rgb_sub_samples):
                out, _ = rgb_model(sub_sample)

                np.save(
                    os.path.join(_OUTPUT_PATH, cls, sample, f"{sample}_{ssi}_rgb.npy"), out.numpy()
                )

                del out

            # Flow
            flow_sample = tf.convert_to_tensor(
                np.load(os.path.join(_SAMPLES_PATH, cls, sample, f"{sample}_flow.npy")),
                dtype=tf.float32,
            )

            transposed = False
            if flow_sample.shape[2] > flow_sample.shape[3]:  # type: ignore
                flow_sample = tf.transpose(flow_sample, (0, 1, 3, 2, 4))
                transposed = True

            flow_sub_samples = []

            final = flow_sample.shape[3] - 224 + 1  # type: ignore
            step = int((flow_sample.shape[3] - 224) / math.floor(flow_sample.shape[3] / 224)) - 1  # type: ignore # pylint: disable=line-too-long
            for i in range(0, final, step if step > 0 else 1):
                flow_sub_samples.append(flow_sample[:, :, :, i : i + 224, :])  # type: ignore

            if transposed:
                for i, sample in enumerate(flow_sub_samples):
                    flow_sub_samples[i] = tf.transpose(sample, (0, 1, 3, 2, 4))

            for ssi, sub_sample in enumerate(flow_sub_samples):
                out, _ = flow_model(sub_sample)

                np.save(
                    os.path.join(_OUTPUT_PATH, cls, sample, f"{sample}_{ssi}_flow.npy"), out.numpy()
                )

                del out

            # Clean up GPU memory after each folder inference
            del rgb_sample, rgb_sub_samples
            del flow_sample, flow_sub_samples
            gc.collect()
            tf.keras.backend.clear_session()


if __name__ == "__main__":
    main()
