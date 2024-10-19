"""
Score metrics
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
# pylint: disable=cell-var-from-loop

import os
import numpy as np

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import tensorflow as tf

tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

class CustomFScore(tf.keras.metrics.Metric):
    """
    Custom F-score metric
    """

    def __init__(
        self,
        classes: dict[int, int],
        betas: dict[int, float],
        confidence_threshold: float,
        fallback_label: int,
        **kwargs,
    ) -> None:
        """
        Initialize the metric

        Args:
            classes: Dict containing the number of samples for each class
            betas: Beta values for each class
        """
        super().__init__(**kwargs)

        if len(betas) > 0:
            assert len(betas) == len(classes), "Number of betas must match the number of classes"
        else:
            betas = {i: 1 for i in classes.keys()}

        self.betas = betas
        self.classes = classes
        self.confidence_threshold = confidence_threshold
        self.fallback_label = fallback_label

        self.precision = [tf.keras.metrics.Precision() for _ in range(len(classes))]
        self.recall = [tf.keras.metrics.Recall() for _ in range(len(classes))]

    def update_state(self, y_true, y_pred, sample_weight=None):
        """
        Update the metric state

        Args:
            y_true: True labels
            y_pred: Predicted logits
            sample_weight: Sample weights
        """

        y_prob = tf.nn.softmax(y_pred)
        y_pred = tf.argmax(y_prob, axis=1)
        
        y_prob = tf.reduce_max(y_prob, axis=1)
        y_pred = tf.where(
            y_prob < self.confidence_threshold,
            self.fallback_label,
            y_pred
        )

        for i in range(len(self.classes)):
            y_true_class = tf.cast(tf.equal(y_true, i), tf.int32)
            y_pred_class = tf.cast(tf.equal(y_pred, i), tf.int32)
            self.precision[i].update_state(y_true_class, y_pred_class, sample_weight=sample_weight)
            self.recall[i].update_state(y_true_class, y_pred_class, sample_weight=sample_weight)

    def result(self):
        """
        Get the metric result
        """

        def _f_beta_score(precision, recall, beta):
            if precision + recall == 0:
                return 0
            return (1 + beta**2) * (precision * recall) / (beta**2 * precision + recall)

        f_scores = []

        for i in range(len(self.classes)):
            precision = self.precision[i].result().numpy()
            recall = self.recall[i].result().numpy()

            f_scores.append(_f_beta_score(precision, recall, beta=self.betas[i]))

        f_score = np.average(f_scores, weights=list(self.classes.values()))

        f_score = tf.constant(f_score, dtype=tf.float32)

        return f_score

