"""
Scrip to fine tune the I3D model on specific data
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
# pylint: disable=cell-var-from-loop

import os
import argparse

from typing import Type

from .utils import Trainer
from . import kinetics

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODELS_MAP: dict[str, Type[Trainer]] = {
    "kinetics": kinetics.Trainer,
}


def main():
    """
    Main function
    """

    parser = argparse.ArgumentParser(description="Fine tune I3D model on custom data")
    parser.add_argument(
        "--model",
        type=str,
        choices=[*MODELS_MAP.keys()],
        required=True,
        help="Model to train",
    )
    parser.add_argument(
        "--data",
        type=str,
        choices=["color", "depth"],
        default="color",
        help="Data type to preprocess",
    )
    parser.add_argument(
        "--k-folds",
        type=int,
        default=5,
        help="Number of folds for k-fold cross validation",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
        help="Number of epochs to train the model",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Batch size for training",
    )
    args = parser.parse_args()

    model_dir = os.path.join(BASE_DIR, args.model)
    input_checkpoints = os.path.join(model_dir, "checkpoints")
    output_checkpoints = os.path.join(model_dir, "finetuned_checkpoints")
    data_dir = os.path.join(model_dir, "data", args.data)
    tmp_dir = os.path.join(model_dir, "tmp")

    for checkpoint in os.listdir(input_checkpoints):
        print(f"Finetuning model: {os.path.join(input_checkpoints, checkpoint)}")

        trainer = MODELS_MAP[args.model](
            os.path.join(input_checkpoints, checkpoint),
            os.path.join(output_checkpoints, checkpoint),
            data_dir,
            tmp_dir,
            args.k_folds,
            args.epochs,
            args.batch_size,
        )

        trainer.initialize()

        trainer.train()

        trainer.save()

        trainer.cleanup()

        print()


if __name__ == "__main__":
    main()
