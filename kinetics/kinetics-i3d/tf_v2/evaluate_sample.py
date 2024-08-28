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

import argparse
import numpy as np
import tensorflow as tf

import i3d

_CHECKPOINT_PATHS_SCRATCH = {
    "rgb": "data/checkpoints/rgb_scratch/model.ckpt",
    "flow": "data/checkpoints/flow_scratch/model.ckpt",
    "rgb600": "data/checkpoints/rgb_scratch_kin600/model.ckpt",
}

_CHECKPOINT_PATHS_IMAGENET = {
    "rgb_imagenet": "data/checkpoints/rgb_imagenet/model.ckpt",
    "flow_imagenet": "data/checkpoints/flow_imagenet/model.ckpt",
}

_LABEL_MAP_PATH = "data/label_map.txt"
_LABEL_MAP_PATH_600 = "data/label_map_600.txt"


def parse_args() -> argparse.Namespace:
    """
    Parse arguments
    """

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--eval-type",
        default="joint",
        choices=["rgb", "flow", "joint" "rg600"],
        help="Type of evaluation",
    )

    parser.add_argument(
        "--imagenet",
        action="store_false",
        help="Use ImageNet pretrained weights. Not availble for rgb600",
    )

    return parser.parse_args()


def main():
    """
    Main function to evaluate I3D on Kinetics.
    """

    tf.random.set_seed(1234)
    np.random.seed(1234)

    args = parse_args()

    eval_type = args.eval_type
    imagenet_pretrained = args.imagenet_pretrained

    if eval_type == "rgb600" and imagenet_pretrained:
        raise ValueError("Kinetics 600 not available for ImageNet pretrained model")

    if imagenet:
        _checkpoint_paths = _CHECKPOINT_IMAGENET_PATHS
    else:
        _checkpoint_paths = _CHECKPOINT_SCRATCH_PATHS

    kinetics_classes = [x.strip() for x in open(_LABEL_MAP_PATH, encoding="utf-8")]

    if "rgb" in eval_type:
        # Create the model
        rgb_model = i3d.InceptionI3d(400, spatial_squeeze=True, final_endpoint="Predictions")

        # Initialize model with dummy input
        rgb_model(tf.zeros((1, 1, 224, 224, 3), dtype=tf.float32))

        # Restore the checkpoint
        checkpoint = tf.compat.v1.train.NewCheckpointReader(_checkpoint_paths["rgb"])

        for var in rgb_model.variables:
            var_name = var.name.split(":")[0]

            # map variables from v1 to v2
            if "/batch_norm/moving_mean/average" in var_name:
                var_name = var_name.replace("/average", "")

            if "/batch_norm/moving_variance/average" in var_name:
                var_name = var_name.replace("/average", "")

            if "/batch_norm/offset" in var_name:
                var_name = var_name.replace("/offset", "/beta")

            # restore variables
            if "RGB/" + var_name in checkpoint.get_variable_to_shape_map():
                tensor = checkpoint.get_tensor("RGB/" + var_name)

                if tensor.ndim == 1 and (
                    "moving_mean" in var.name or "moving_variance" in var.name
                ):
                    tensor = tensor.reshape((1, 1, 1, 1, tensor.shape[0]))

                var.assign(tensor)

        print("RGB checkpoint restored")

        rgb_sample = tf.convert_to_tensor(np.load(_SAMPLE_PATHS["rgb"]), dtype=tf.float32)

        out_predictions = rgb_model(rgb_sample)[0][0]  # type: ignore

        sorted_indices = np.argsort(out_predictions)[::-1]

        print("Top classes and probabilities")
        for index in sorted_indices[:20]:
            print(out_predictions[index], kinetics_classes[index])

    if "flow" in eval_type:
        flow_model = i3d.InceptionI3d(
            400,
            spatial_squeeze=True,
            final_endpoint="Predictions",
            is_training=False,
            dropout_keep_prob=1.0,
        )

        # tf.train.Checkpoint(model=flow_model).restore(_checkpoint_paths["flow"]).expect_partial()
        # print("Flow checkpoint restored")

        flow_sample = np.load(_SAMPLE_PATHS["flow"])
        print(f"Flow data loaded, shape={str(flow_sample.shape)}")  # type: ignore

        flow_sample = tf.convert_to_tensor(flow_sample, dtype=tf.float32)

        out_predictions = flow_model(flow_sample)[0][0]  # type: ignore

        sorted_indices = np.argsort(out_predictions)[::-1]

        print("\nTop classes and probabilities")
        for index in sorted_indices[:20]:
            print(out_predictions[index], kinetics_classes[index])


if __name__ == "__main__":
    main()
