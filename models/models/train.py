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
from . import vivit
from . import hmm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODELS_MAP: dict[str, Type[Trainer]] = {
    "kinetics": kinetics.Trainer,
    "vivit": vivit.Trainer,
    "hmm": hmm.Trainer,
}


def main():
    """
    Main function
    """

    parser = argparse.ArgumentParser(description="Fine tune I3D model on custom data")
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        choices=[*MODELS_MAP.keys()],
        required=True,
        help="Model to train",
    )
    parser.add_argument(
        "--data",
        "-d",
        type=str,
        choices=["color", "depth"],
        required=True,
        help="Data type to preprocess",
    )
    parser.add_argument(
        "--learning-rates",
        "-lr",
        type=str,
        required=True,
        help="Learning rates to search",
    )
    parser.add_argument(
        "--confidence-thresholds",
        "-ct",
        type=str,
        required=True,
        help="Confidence thresholds to search",
    )
    args = parser.parse_args()
    args.learning_rates = list(map(float, args.learning_rates.split(",")))
    args.confidence_thresholds = list(map(float, args.confidence_thresholds.split(",")))

    model_dir = os.path.join(BASE_DIR, args.model)
    input_checkpoints = os.path.join(model_dir, "checkpoints", "base")
    output_checkpoints = os.path.join(model_dir, "checkpoints", args.data)
    data_dir = os.path.join(model_dir, "data", "train", args.data)
    tmp_dir = os.path.join(model_dir, "tmp")

    for checkpoint in os.listdir(input_checkpoints):
        print(f"Finetuning model: {os.path.join(input_checkpoints, checkpoint)}")

        trainer = MODELS_MAP[args.model](
            os.path.join(input_checkpoints, checkpoint),
            os.path.join(output_checkpoints, checkpoint),
            data_dir,
            tmp_dir,
            args.learning_rates,
            args.confidence_thresholds,
        )

        trainer.initialize()

        trainer.search()

        trainer.train()

        trainer.save()

        trainer.cleanup()

        print()


if __name__ == "__main__":
    main()
