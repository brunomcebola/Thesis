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

import os
import math
import logging
import numpy as np
import tqdm

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf  # pylint: disable=wrong-import-position

import i3d  # pylint: disable=wrong-import-position

_SAMPLES_PATH = "output"

_LABEL_MAP_PATH = "label_map.txt"

_CHECKPOINTS_PATH = "checkpoints"

_SIZE = 224


def main():
    """
    Main function to evaluate I3D on Kinetics.
    """

    # hide tf logs
    logging.basicConfig(level=logging.INFO)

    kinetics_classes = [x.strip() for x in open(_LABEL_MAP_PATH, encoding="utf-8")]

    # Instantiate the model for RGB
    rgb_model = i3d.InceptionI3d(400, spatial_squeeze=True, final_endpoint="Logits")

    # Restore the checkpoint
    tf.train.Checkpoint(model=rgb_model).restore(
        os.path.join(_CHECKPOINTS_PATH, "rgb", "model.ckpt")
    ).expect_partial()

    # Instantiate the model for flow
    flow_model = i3d.InceptionI3d(400, spatial_squeeze=True, final_endpoint="Logits")

    # Restore the checkpoint
    tf.train.Checkpoint(model=flow_model).restore(
        os.path.join(_CHECKPOINTS_PATH, "flow", "model.ckpt")
    ).expect_partial()

    # Perform the inferences
    inferences = []
    for folder in tqdm.tqdm(
        [
            folder
            for folder in os.listdir(_SAMPLES_PATH)
            if os.path.isdir(os.path.join(_SAMPLES_PATH, folder))
        ]
    ):
        # RGB prediction
        if not os.path.exists(os.path.join(_SAMPLES_PATH, folder, f"{folder}_rgb.npy")):
            raise FileNotFoundError(f"RGB sample not found: {folder}_rgb.npy")

        rgb_sample = tf.convert_to_tensor(
            np.load(os.path.join(_SAMPLES_PATH, folder, f"{folder}_rgb.npy")), dtype=tf.float32
        )

        transposed = False
        if rgb_sample.shape[2] > rgb_sample.shape[3]:  # type: ignore
            rgb_sample = tf.transpose(rgb_sample, (0, 1, 3, 2, 4))
            transposed = True

        rgb_samples = []

        final = rgb_sample.shape[3] - 224 + 1  # type: ignore
        step = int((rgb_sample.shape[3] - 224) / math.floor(rgb_sample.shape[3] / 224)) - 1  # type: ignore # pylint: disable=line-too-long
        for i in range(0, final, step if step > 0 else 1):
            rgb_samples.append(rgb_sample[:, :, :, i : i + 224, :])  # type: ignore

        if transposed:
            for i, sample in enumerate(rgb_samples):
                rgb_samples[i] = tf.transpose(sample, (0, 1, 3, 2, 4))

        rgb_logits, _ = rgb_model(rgb_samples[0])
        for sample in rgb_samples[1:]:
            logits, _ = rgb_model(sample)
            rgb_logits += logits

        rgb_predictions = tf.nn.softmax(rgb_logits)[0]

        rgb_index = np.argsort(rgb_predictions)[::-1][0]
        rgb_prediction = rgb_predictions[rgb_index]
        rgb_label = kinetics_classes[rgb_index]

        # Flow prediction
        if not os.path.exists(os.path.join(_SAMPLES_PATH, folder, f"{folder}_flow.npy")):
            raise FileNotFoundError(f"Flow sample not found: {folder}_flow.npy")

        flow_sample = tf.convert_to_tensor(
            np.load(os.path.join(_SAMPLES_PATH, folder, f"{folder}_flow.npy")), dtype=tf.float32
        )

        transposed = False
        if flow_sample.shape[2] > flow_sample.shape[3]:  # type: ignore
            flow_sample = tf.transpose(flow_sample, (0, 1, 3, 2, 4))
            transposed = True

        flow_samples = []

        final = flow_sample.shape[3] - 224 + 1  # type: ignore
        step = int((flow_sample.shape[3] - 224) / math.floor(flow_sample.shape[3] / 224)) - 1  # type: ignore # pylint: disable=line-too-long
        for i in range(0, final, step if step > 0 else 1):
            flow_samples.append(flow_sample[:, :, :, i : i + 224, :])  # type: ignore

        if transposed:
            for i, sample in enumerate(flow_samples):
                flow_samples[i] = tf.transpose(sample, (0, 1, 3, 2, 4))

        flow_logits, _ = flow_model(flow_samples[0])
        for sample in flow_samples[1:]:
            logits, _ = flow_model(sample)
            flow_logits += logits

        flow_predictions = tf.nn.softmax(flow_logits)[0]

        flow_index = np.argsort(flow_predictions)[::-1][0]
        flow_prediction = flow_predictions[flow_index]
        flow_label = kinetics_classes[flow_index]

        # Joint prediction
        joint_logits = rgb_logits + flow_logits
        joint_predictions = tf.nn.softmax(joint_logits)[0]

        joint_index = np.argsort(joint_predictions)[::-1][0]
        joint_prediction = joint_predictions[joint_index]
        joint_label = kinetics_classes[joint_index]

        inferences.append(
            (
                folder,
                (rgb_label, rgb_prediction),
                (flow_label, flow_prediction),
                (joint_label, joint_prediction),
            )
        )

    for inference in inferences:
        print(f"\nPrediction for {inference[0]}:")
        print(f"\tRGB: '{inference[1][0]}' ({inference[1][1]})")
        print(f"\tFlow: '{inference[2][0]}' ({inference[2][1]})")
        print(f"\tJoint: '{inference[3][0]}' ({inference[3][1]})")


if __name__ == "__main__":
    main()
