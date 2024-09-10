"""
This module contains the handlers for the nodes
"""

from __future__ import annotations


import os
from pathlib import Path

from .. import logger as _logger

DATASETS_DIR = os.path.join(os.environ["BASE_DIR"], "datasets")


class Dataset:
    """
    Class representing a dataset
    """

    _path: Path

    STRUCTURE: dict[str, dict] = {
        "raw": {},
        "processed": {
            "train": {},
            "val": {},
            "test": {},
        },
    }

    def __init__(
        self,
        name: str,
    ) -> None:
        """
        Initializes the dataset

        Args:
            name (str): The name of the dataset

        Raises:
            ValueError: If no name is provided or
            if the name is invalid
        """

        # Ensure name is provided
        if not name:
            raise ValueError("No name provided.")

        # Ensure name is valid
        if not name.isidentifier():
            raise ValueError("Invalid name provided.")


        path = Path(DATASETS_DIR).joinpath(name)

        # Ensure structure of dataset
        for dir_name, dir_content in Dataset.STRUCTURE.items():
            if not path.joinpath(dir_name).is_dir():
                os.makedirs(path.joinpath(dir_name), exist_ok=True)

            for subdir_name, _ in dir_content.items():
                if not path.joinpath(name, subdir_name).is_dir():
                    os.makedirs(path.joinpath(dir_name, subdir_name), exist_ok=True)

        self._path = path

    # Instance properties

    @property
    def name(self) -> str:
        """
        Returns the name of the dataset
        """

        return self._path.name

    @property
    def path(self) -> Path:
        """
        Returns the path of the dataset
        """

        return self._path


class DatasetsHandler:
    """
    Class used to handle the datasets
    """

    _datasets: list[Dataset]

    def __init__(self) -> None:
        """
        Initializes the handler
        """

        self._datasets = []

        _logger.info("Initializing datasets...")

        # Load datasets

        success = 0
        fail = 0
        for dataset_name in os.listdir(DATASETS_DIR):
            fail += 1

            try:
                self.__add_dataset(dataset_name)
            except Exception as e:  # pylint: disable=broad-except
                _logger.warning("Unable to initialize dataset - %s.", e)
                continue

            fail -= 1
            success += 1

        _logger.info(
            "Datasets initialized - Total: %s, Success: %s, Fail: %s.",
            success + fail,
            success,
            fail,
        )

    # Instance private methods

    def __add_dataset(
        self,
        dataset_name: str,
    ) -> Dataset:
        """
        Adds a new node to the list and connects to it

        Args:
            name (str): The name of the dataset

        Returns:
            Dataset: The added dataset

        Raises:
            ValueError: If the dataset is already registered
        """

        dataset = Dataset(dataset_name)

        # Ensure dataset is not already registered
        if dataset.name in [dataset.name for dataset in self._datasets]:
            raise ValueError(f"Dataset '{dataset.name}' already registered.")

        self._datasets.append(dataset)

        return dataset

    # Instance public methods

    def get_datasets(self) -> list[str]:
        """
        Returns the list of datasets
        """

        return [dataset.name for dataset in self._datasets]

    def create_dataset(
        self,
        dataset_name: str,
    ) -> None:
        """
        Creates a new dataset

        Args:
            dataset_name (str): The name of the dataset

        Raises:
            ValueError: If no name is provided or
            if the dataset cannot be created for any reason
        """

        if not dataset_name:
            raise ValueError("No name provided.")

        _logger.info("Creating new dataset...")
        try:
            dataset = self.__add_dataset(dataset_name)
        except Exception as e:  # pylint: disable=broad-except
            _logger.warning("Unable to create dataset - %s.", e)
            raise

        _logger.info("Created new dataset '%s' (%s).", dataset.name, dataset.path)


#  Create base folder if it doesn't exist
os.makedirs(DATASETS_DIR, exist_ok=True)

# Create nodes handler
datasets_handler = DatasetsHandler()
