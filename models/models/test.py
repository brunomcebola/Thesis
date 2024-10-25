"""
Scrip to test the I3D model on specific data
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order

from __future__ import annotations

import os
import argparse

from typing import Type

from .utils import Tester
from . import kinetics
from . import vivit
from . import hmm

###

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODELS_MAP: dict[str, Type[Tester]] = {
    "kinetics": kinetics.Tester,
    "vivit": vivit.Tester,
    "hmm": hmm.Tester,
}

###


def main():
    """
    Main function to evaluate I3D on Kinetics.
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
        "--confidence-threshold",
        "-c",
        type=float,
        required=True,
        help="Confidence threshold for the F-score",
    )
    args = parser.parse_args()

    model_dir = os.path.join(BASE_DIR, args.model)
    checkpoints = os.path.join(model_dir, "checkpoints", args.data)
    data_dir = os.path.join(model_dir, "data", "test", args.data)
    tests_dir = os.path.join(model_dir, "tests", args.data)

    # Get combination of checkpoints
    checkpoints_groups: dict[str, dict[str, str]] = {}
    for checkpoint in os.listdir(checkpoints):
        base, stream = checkpoint.split(".")

        checkpoint_path = os.path.join(checkpoints, checkpoint)

        checkpoints_groups[base] = checkpoints_groups.get(base, {})
        checkpoints_groups[base][stream] = os.path.join(checkpoint_path, "model.ckpt")

    # Perform the inferences for each combination of checkpoints
    for group in checkpoints_groups.items():
        print(f"Evaluating checkpoints group '{group[0]}'")

        tester = MODELS_MAP[args.model](
            group,
            data_dir,
            tests_dir,
            args.confidence_threshold,
            2
        )

        tester.initialize()

        tester.test()

        tester.save()

if __name__ == "__main__":
    main()
