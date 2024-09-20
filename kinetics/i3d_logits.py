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
"""Inception-v1 Inflated 3D ConvNet used for Kinetics CVPR paper.

The model is introduced in:

  Quo Vadis, Action Recognition? A New Model and the Kinetics Dataset
  Joao Carreira, Andrew Zisserman
  https://arxiv.org/pdf/1705.07750v1.pdf.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sonnet as snt
import tensorflow as tf


class Unit3D(snt.Module):
    """Basic unit containing Conv3D + BatchNorm + non-linearity."""

    def __init__(
        self,
        output_channels,
        kernel_shape=(1, 1, 1),
        stride=(1, 1, 1),
        activation_fn=tf.nn.relu,
        use_batch_norm=True,
        use_bias=False,
        is_training=False,
        name="unit_3d",
    ):
        """
        Initializes Unit3D module.

        Args:
            output_channels: number of output channels (int).
            kernel_shape: shape of the convolutional kernel (iterable of 3 ints).
            stride: shape of the convolutional stride (iterable of 3 ints).
            activation_fn: activation function (callable).
            use_batch_norm: whether to use batch normalization (boolean).
            use_bias: whether to use bias (boolean).
            is_training: whether to use training mode for snt.BatchNorm (boolean).
            name: name of the module (string).
        """
        super(Unit3D, self).__init__(name=name)

        self._use_batch_norm = use_batch_norm
        self._activation_fn = activation_fn
        self._is_training = is_training

        # layers

        self.conv3d = snt.Conv3D(
            output_channels=output_channels,
            kernel_shape=kernel_shape,
            stride=stride,
            padding="SAME",
            with_bias=use_bias,
            name="conv_3d",
        )

        self.batch_norm = snt.BatchNorm(
            create_scale=False,
            create_offset=True,
        )

    def __call__(self, net):
        """
        Connects the module to inputs.

        Args:
          net: Inputs to the Unit3D component.

        Returns:
          Outputs from the module.
        """
        net = self.conv3d(net)

        if self._use_batch_norm:
            net = self.batch_norm(net, is_training=self._is_training, test_local_stats=False)

        if self._activation_fn is not None:
            net = self._activation_fn(net)

        return net


class Logits(snt.Module):
    """
    Logits layer.
    """

    def __init__(
        self,
        num_classes,
        is_training=False,
        dropout_keep_prob=1.0,
        name="logits",
    ):
        super(Logits, self).__init__(name=name)

        self._dropout_keep_prob = dropout_keep_prob

        self.logits = Unit3D(
            output_channels=num_classes,
            kernel_shape=[1, 1, 1],
            activation_fn=None,
            use_batch_norm=False,
            use_bias=True,
            is_training=is_training,
            name="Conv3d_0c_1x1",
        )

    def __call__(self, net):
        net = tf.nn.avg_pool3d(
            net,
            ksize=[1, 2, 7, 7, 1],
            strides=[1, 1, 1, 1, 1],
            padding="VALID",
        )

        net = tf.nn.dropout(
            net,
            1 - self._dropout_keep_prob,
        )

        net = self.logits(net)

        net = tf.squeeze(net, [2, 3], name="SpatialSqueeze")

        return tf.reduce_mean(net, axis=1)


class InceptionI3dLogits(snt.Module):
    def __init__(
        self,
        num_classes,
        is_training=False,
        dropout_keep_prob=1.0,
    ):
        if not 0 < dropout_keep_prob <= 1:
            raise ValueError("dropout_keep_prob must be in range (0, 1]")

        super(InceptionI3dLogits, self).__init__(name="inception_i3d_logits")

        # Logits

        self.Logits = Logits(  # pylint: disable=invalid-name
            num_classes=num_classes,
            is_training=is_training,
            dropout_keep_prob=dropout_keep_prob,
            name="Logits",
        )

    def __call__(self, net):
        """Connects the model to inputs.

        Args:
          net: Inputs to the model, which should have dimensions
              `batch_size` x `num_frames` x 224 x 224 x `num_channels`.

        Returns:
          A tuple consisting of:
            1. Network output at location `self._final_endpoint`.
            2. Dictionary containing all endpoints up to `self._final_endpoint`,
               indexed by endpoint name.

        Raises:
            ValueError:
                if net shape is not `batch_size` x `num_frames` x 224 x 224 x `num_channels`
        """

        if len(net.shape) != 5 or net.shape[2] != 7 or net.shape[3] != 7:
            raise ValueError(
                "Input tensor shape must be [batch_size, num_frames, 224, 224, num_channels]"
            )

        endpoints = {}

        net = self.Logits(net)

        endpoints["Logits"] = net

        return net, endpoints
