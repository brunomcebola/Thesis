"""
Isolates the I3D logits module from the rest of the I3D model.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sonnet as snt
import tensorflow as tf


class Unit3D(snt.Module):
    """Unit3D module"""

    def __init__(
        self,
        output_channels,
        kernel_shape=(1, 1, 1),
        stride=(1, 1, 1),
        name="unit_3d",
    ):

        super(Unit3D, self).__init__(name=name)

        # layers

        self.conv3d = snt.Conv3D(
            output_channels=output_channels,
            kernel_shape=kernel_shape,
            stride=stride,
            name="conv_3d",
        )

    def __call__(self, net):

        net = self.conv3d(net)

        return net


class Logits(snt.Module):
    """Logits module"""

    def __init__(
        self,
        num_classes,
        dropout_keep_prob=1.0,
        name="logits",
    ):
        super(Logits, self).__init__(name=name)

        self._dropout_keep_prob = dropout_keep_prob

        self.logits = Unit3D(
            output_channels=num_classes,
            kernel_shape=[1, 1, 1],
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

        net = tf.reduce_mean(net, axis=1)

        return net


class InceptionI3dLogits(snt.Module):
    """InceptionI3DLogits module"""

    def __init__(
        self,
        num_classes,
        dropout_keep_prob=1.0,
    ):
        super(InceptionI3dLogits, self).__init__(name="inception_i3d_logits")

        self.Logits = Logits(  # pylint: disable=invalid-name
            num_classes=num_classes,
            dropout_keep_prob=dropout_keep_prob,
            name="Logits",
        )

    @tf.function
    def __call__(self, net):

        endpoints = {}

        net = self.Logits(net)

        endpoints["Logits"] = net

        return net, endpoints
