"""
Classification Head for ViViT
"""

import tensorflow as tf

class ViViTLogits(tf.Module):
    def __init__(self, num_classes, name="vivit_logits"):
        super(ViViTLogits, self).__init__(name=name)

        self.pool = tf.keras.layers.GlobalAveragePooling1D()
        self.logits = tf.keras.layers.Dense(num_classes, name="logits")

    def __call__(self, net):
        net = self.pool(net)
        net = self.logits(net)
        
        return net, None