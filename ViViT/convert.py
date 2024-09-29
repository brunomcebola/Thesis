import os
import shutil
import torch
from tqdm import tqdm

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf  # pylint: disable=wrong-import-position
from transformers import VivitConfig, VivitForVideoClassification  # pylint: disable=wrong-import-position


def extract_tf_weights(tf_model):
    """
    Extract TensorFlow weights from a TensorFlow model.
    """

    variables = tf_model.variables
    tf_weights = {}
    for var in variables:
        var_name = var.name.replace(":0", "")
        tf_weights[var_name] = var.numpy()
    return tf_weights


def load_tf_to_pytorch(tf_weights, pytorch_model):
    """
    Load TensorFlow weights into a PyTorch model.
    """

    pytorch_params = dict(pytorch_model.named_parameters())

    for name, param in pytorch_params.items():
        print(f"Variable Name: {name}, Shape: {param.data.shape}")
        tf_name = name.replace(".", "/")

        if tf_name in tf_weights:
            tf_weight = tf_weights[tf_name]
            if tf_weight.shape == param.data.shape:
                param.data = torch.from_numpy(tf_weight).float()


def main():
    """
    Convert TensorFlow weights to PyTorch weights.
    """

    os.makedirs("models", exist_ok=True)

    for saved_model in tqdm(os.listdir("tf_saved_models")):

        tf_model = tf.saved_model.load(f"tf_saved_models/{saved_model}")

        tf_weights = extract_tf_weights(tf_model)

        config = VivitConfig.from_json_file(f"configs/{saved_model}.json")

        pytorch_model = VivitForVideoClassification(config)

        load_tf_to_pytorch(tf_weights, pytorch_model)

        shutil.rmtree(f"models/{saved_model}", ignore_errors=True)

        pytorch_model.save_pretrained(f"models/{saved_model}")


if __name__ == "__main__":
    main()
