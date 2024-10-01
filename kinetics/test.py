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
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix


os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf  # pylint: disable=wrong-import-position

import i3d  # pylint: disable=wrong-import-position

###

DATA = "color"
CHECKPOINT = "3_color_logits"

###

SAMPLES_PATH = f"npy/{DATA}"
RGB_CHECKPOINT_PATH = f"checkpoints/rgb_{CHECKPOINT}/model.ckpt"
FLOW_CHECKPOINT_PATH = f"checkpoints/flow_{CHECKPOINT}/model.ckpt"


def sub_sample(sample: tf.Tensor) -> list[tf.Tensor]:
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


def main():
    """
    Main function to evaluate I3D on Kinetics.
    """
    print("Testing Google Inception-v1 Inflated 3D ConvNet\n")

    # Ensure both checkpoints exist and have the same classes
    assert os.path.exists(f"{RGB_CHECKPOINT_PATH}.index")
    assert os.path.exists(f"{RGB_CHECKPOINT_PATH}.data-00000-of-00001")
    assert os.path.exists(f"{FLOW_CHECKPOINT_PATH}.index")
    assert os.path.exists(f"{FLOW_CHECKPOINT_PATH}.data-00000-of-00001")

    with open(RGB_CHECKPOINT_PATH.replace(".ckpt", ".txt"), encoding="utf-8") as file:
        rgb_classes = [x.strip() for x in file]

    with open(FLOW_CHECKPOINT_PATH.replace(".ckpt", ".txt"), encoding="utf-8") as file:
        flow_classes = [x.strip() for x in file]

    assert rgb_classes == flow_classes

    classes = rgb_classes

    print(f"Classes: {len(classes)} {classes}")

    # Ensure the samples path exists for all classes
    # and that each class has at least one sample
    # of type 'rgb' and 'flow'
    rgb_samples_infos = []
    flow_samples_infos = []

    for i, cls in enumerate(classes):
        assert os.path.exists(os.path.join(SAMPLES_PATH, cls))
        assert os.path.isdir(os.path.join(SAMPLES_PATH, cls))
        assert len(os.listdir(os.path.join(SAMPLES_PATH, cls))) > 0

        for sample in os.listdir(os.path.join(SAMPLES_PATH, cls)):
            assert os.path.isdir(os.path.join(SAMPLES_PATH, cls, sample))
            assert os.path.exists(os.path.join(SAMPLES_PATH, cls, sample, f"{sample}_rgb.npy"))
            assert os.path.exists(os.path.join(SAMPLES_PATH, cls, sample, f"{sample}_flow.npy"))

            rgb_samples_infos.append(
                (os.path.join(SAMPLES_PATH, cls, sample, f"{sample}_rgb.npy"), i)
            )
            flow_samples_infos.append(
                (os.path.join(SAMPLES_PATH, cls, sample, f"{sample}_flow.npy"), i)
            )

    assert len(rgb_samples_infos) == len(flow_samples_infos)

    print(f"Samples: {len(rgb_samples_infos)}\n")

    # Load models
    rgb_model = i3d.InceptionI3d(3, spatial_squeeze=True, final_endpoint="Logits")
    tf.train.Checkpoint(model=rgb_model).restore(RGB_CHECKPOINT_PATH).expect_partial()

    flow_model = i3d.InceptionI3d(3, spatial_squeeze=True, final_endpoint="Logits")
    tf.train.Checkpoint(model=flow_model).restore(FLOW_CHECKPOINT_PATH).expect_partial()

    print("Models loaded successfully\n")

    # Perform the inferences
    inferences = []

    for rgb_sample_info, flow_sample_info in tqdm.tqdm(
        zip(rgb_samples_infos, flow_samples_infos), total=len(rgb_samples_infos), desc="Testing"
    ):
        # rgb inference
        rgb_sample = tf.convert_to_tensor(np.load(rgb_sample_info[0]), dtype=tf.float32)
        rgb_sub_samples = sub_sample(rgb_sample)

        rgb_logits, _ = rgb_model(rgb_sub_samples[0])
        if len(rgb_sub_samples) > 1:
            for sample in rgb_sub_samples[1:]:
                logits, _ = rgb_model(sample)
                rgb_logits += logits

        del rgb_sample, rgb_sub_samples
        gc.collect()
        tf.keras.backend.clear_session()

        rgb_predictions = tf.nn.softmax(rgb_logits)[0]
        rgb_index = np.argsort(rgb_predictions)[::-1][0]
        rgb_prediction = rgb_predictions[rgb_index]

        # flow inference
        flow_sample = tf.convert_to_tensor(np.load(flow_sample_info[0]), dtype=tf.float32)
        flow_sub_samples = sub_sample(flow_sample)

        flow_logits, _ = flow_model(flow_sub_samples[0])
        if len(flow_sub_samples) > 1:
            for sample in flow_sub_samples[1:]:
                logits, _ = flow_model(sample)
                flow_logits += logits

        del flow_sample, flow_sub_samples
        gc.collect()
        tf.keras.backend.clear_session()

        flow_predictions = tf.nn.softmax(flow_logits)[0]
        flow_index = np.argsort(flow_predictions)[::-1][0]
        flow_prediction = flow_predictions[flow_index]

        # joint inference

        joint_logits = rgb_logits + flow_logits

        del rgb_logits, flow_logits
        gc.collect()
        tf.keras.backend.clear_session()

        joint_predictions = tf.nn.softmax(joint_logits)[0]
        joint_index = np.argsort(joint_predictions)[::-1][0]
        joint_prediction = joint_predictions[joint_index]

        del joint_logits
        gc.collect()
        tf.keras.backend.clear_session()

        inferences.append(
            (
                rgb_sample_info,
                (rgb_index, rgb_prediction),
                (flow_index, flow_prediction),
                (joint_index, joint_prediction),
            )
        )

    for inference in inferences:
        print(f"\nPrediction for {inference[0][0]}:")
        print(f"\tReal: '{inference[0][1]}'")
        print(f"\tRGB: '{inference[1][0]}' ({inference[1][1]})")
        print(f"\tFlow: '{inference[2][0]}' ({inference[2][1]})")
        print(f"\tJoint: '{inference[3][0]}' ({inference[3][1]})")

    # Generate confusion matrix
    true_labels = np.array([i[1] for i, _, _, _ in inferences])
    rgb_predicted_labels = np.array([i[0] for _, i, _, _ in inferences])
    flow_predicted_labels = np.array([i[0] for _, _, i, _ in inferences])
    joint_predicted_labels = np.array([i[0] for _, _, _, i in inferences])

    cm_rgb = confusion_matrix(true_labels, rgb_predicted_labels)
    cm_flow = confusion_matrix(true_labels, flow_predicted_labels)
    cm_joint = confusion_matrix(true_labels, joint_predicted_labels)

    fig, axs = plt.subplots(1, 3, figsize=(15, 5))

    sns.heatmap(cm_rgb, annot=True, fmt="d", cmap="Blues", ax=axs[0], cbar=False)
    axs[0].set_title("RGB")
    axs[0].set_xlabel("Predicted")
    axs[0].set_ylabel("True")

    sns.heatmap(cm_flow, annot=True, fmt="d", cmap="Blues", ax=axs[1], cbar=False)
    axs[1].set_title("Flow")
    axs[1].set_xlabel("Predicted")
    axs[1].set_ylabel("True")

    sns.heatmap(cm_joint, annot=True, fmt="d", cmap="Blues", ax=axs[2], cbar=False)
    axs[2].set_title("Joint")
    axs[2].set_xlabel("Predicted")
    axs[2].set_ylabel("True")

    plt.show()

if __name__ == "__main__":
    main()
