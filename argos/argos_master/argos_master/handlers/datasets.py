"""
This module contains the handlers for the nodes
"""

from __future__ import annotations


import os
import shutil
from pathlib import Path
import io
import cv2
import numpy as np

from .. import logger as _logger

DATASETS_DIR = os.path.join(os.environ["BASE_DIR"], "datasets")


class Dataset:
    """
    Class representing a dataset
    """

    _path: Path
    _clients: int

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
        self._clients = 0

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

    @property
    def clients(self) -> int:
        """
        Returns the number of clients using the dataset
        """

        return self._clients

    @property
    def raw_images(self) -> list[str]:
        """
        Returns the list of raw images in the dataset
        """

        return sorted(os.listdir(self._path.joinpath("raw")))

    # Instance public methods

    def register_client(self) -> None:
        """
        Registers a client to the dataset
        """

        self._clients += 1

    def unregister_client(self) -> None:
        """
        Unregisters a client from the dataset
        """

        self._clients -= 1

        if self._clients < 0:
            self._clients = 0

    def save_raw_data(
        self,
        data: np.ndarray,
        filename: str,
    ) -> None:
        """
        Saves raw data to the dataset

        Args:
            data (np.ndarray): The data to save
            filename (str): The name of the file

        Raises:
            ValueError: If no data is provided or
            if no filename is provided
        """

        if data is None:
            raise ValueError("No data provided.")

        if not filename:
            raise ValueError("No filename provided.")

        # Ensure .npy
        if not filename.endswith(".npy"):
            filename += ".npy"

        np.save(self._path.joinpath("raw", filename), data)

    def get_raw_image(self, filename: str) -> bytes:
        """
        Returns a raw color image

        Args:
            filename (str): The name of the file

        Returns:
            bytes: The image as bytes

        Raises:
            ValueError: If no filename is provided or
            if the filename is invalid
        """

        if not filename:
            raise ValueError("No filename provided.")

        if not filename.endswith(".npy"):
            raise ValueError("Invalid filename provided.")

        image = np.load(self._path.joinpath("raw", filename))

        if "color" in filename:
            # Convert BGR to RGB
            _, buffer = cv2.imencode(".png", image)
            img = io.BytesIO(buffer.tobytes())

        elif "depth" in filename:
            # Normalize depth image
            image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
            image = np.uint8(image)
            image = cv2.applyColorMap(image, cv2.COLORMAP_JET)
            _, buffer = cv2.imencode(".png", image)
            img = io.BytesIO(buffer.tobytes())

        else:
            raise ValueError("Invalid filename provided.")

        return img.getvalue()


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

    def __delete_dataset(self, dataset_name: str) -> Dataset:
        """
        Deletes a dataset

        Args:
            dataset_name (str): The name of the dataset

        Raises:
            ValueError: If the dataset is not found

        Note: The actual deletion of the dataset is not done here
        """

        dataset = next(
            (dataset for dataset in self._datasets if dataset.name == dataset_name),
            None,
        )

        if not dataset:
            raise ValueError(f"Dataset '{dataset_name}' not found.")

        if dataset.clients:
            raise ValueError("Dataset is in use.")

        self._datasets.remove(dataset)

        return dataset

    # Instance public methods

    def get_datasets(self) -> list[str]:
        """
        Returns the list of datasets
        """

        return [dataset.name for dataset in self._datasets]

    def get_dataset(self, dataset_name: str) -> Dataset:
        """
        Returns a dataset

        Args:
            dataset_name (str): The name of the dataset

        Returns:
            Dataset: The dataset

        Raises:
            ValueError: If no name is provided or
            if the dataset is not found
        """

        # TODO: remove this by passing list to dict

        if not dataset_name:
            raise ValueError("No name provided.")

        dataset = next(
            (dataset for dataset in self._datasets if dataset.name == dataset_name),
            None,
        )

        if not dataset:
            raise ValueError(f"Dataset '{dataset_name}' not found.")

        return dataset

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

    def edit_dataset(
        self,
        dataset_name: str,
        new_name: str,
    ) -> None:
        """
        Edits a dataset

        Args:
            dataset_name (str): The name of the dataset
            new_name (str): The new name of the dataset

        Raises:
            ValueError: If no name is provided or
            if the dataset is not found or
            if the new name is invalid or
            if the new name is already in use
        """

        if not new_name:
            raise ValueError("No new name provided.")

        _logger.info("Editing dataset...")

        self.__delete_dataset(dataset_name)

        try:
            shutil.move(
                os.path.join(DATASETS_DIR, dataset_name),
                os.path.join(DATASETS_DIR, new_name),
            )
        except Exception as e:  # pylint: disable=broad-except
            _logger.warning("Unable to edit dataset - %s.", e)
            self.__add_dataset(dataset_name)
            raise

        try:
            self.__add_dataset(new_name)
        except Exception as e:  # pylint: disable=broad-except
            _logger.warning("Unable to edit dataset - %s.", e)
            shutil.move(
                os.path.join(DATASETS_DIR, new_name),
                os.path.join(DATASETS_DIR, dataset_name),
            )
            self.__add_dataset(dataset_name)
            raise

        _logger.info("Edited dataset '%s' to '%s'.", dataset_name, new_name)

    def delete_dataset(self, dataset_name: str) -> None:
        """
        Deletes a dataset

        Args:
            dataset_name (str): The name of the dataset
        """

        _logger.info("Deleting dataset...")

        dataset = self.__delete_dataset(dataset_name)

        shutil.rmtree(dataset.path)

        _logger.info("Deleted dataset '%s'.", dataset.name)

    def get_dataset_raw_images(self, dataset_name: str) -> list[str]:
        """
        Returns the list of raw images in a dataset

        Args:
            dataset_name (str): The name of the dataset

        Returns:
            list[str]: The list of raw images

        Raises:
            ValueError: If no name is provided or
            if the dataset is not found
        """

        dataset = next(
            (dataset for dataset in self._datasets if dataset.name == dataset_name),
            None,
        )

        if not dataset:
            raise ValueError(f"Dataset '{dataset_name}' not found.")

        return dataset.raw_images

    def get_dataset_raw_image(self, dataset_name: str, filename: str) -> bytes:
        """
        Returns a raw image

        Args:
            dataset_name (str): The name of the dataset
            filename (str): The name of the file

        Returns:
            bytes: The image as bytes

        Raises:
            ValueError: If no name is provided or
            if the dataset is not found
        """

        dataset = next(
            (dataset for dataset in self._datasets if dataset.name == dataset_name),
            None,
        )

        if not dataset:
            raise ValueError(f"Dataset '{dataset_name}' not found.")

        return dataset.get_raw_image(filename)


#  Create base folder if it doesn't exist
os.makedirs(DATASETS_DIR, exist_ok=True)

# Create nodes handler
datasets_handler = DatasetsHandler()
