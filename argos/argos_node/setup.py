"""
This is the setup.py file for the argos_node package.
"""

import os
import shutil
import subprocess
from setuptools import setup, find_packages
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel


# Function to read requirements from a file
def read_requirements(filename) -> list[str]:
    """
    Read requirements from a file.
    """
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


# Define the custom bdist_wheel command
class bdist_wheel(_bdist_wheel):  # pylint: disable=invalid-name
    """
    Custom bdist_wheel command to download production dependencies.
    """

    def run(self):
        # Ensure the dependencies directory exists

        # Download production dependencies
        subprocess.check_call(
            [
                "pip",
                "download",
                "-r",
                "requirements.txt",
                "-d",
                "dist",
                "--platform",
                "linux_armv7l",
                "--only-binary=:all:",
                "--extra-index-ur",
                "https://www.piwheels.org/simple",
            ]
        )

        # Create the wheel as usual
        super().run()


setup(
    name="argos_node",
    version="2.0.0",
    author="Bruno Cebola",
    author_email="bruno.m.cebola@tecnico.ulisboa.pt",
    description="ARGOS, Automated Real-time Guardian Observation System",
    long_description=open(
        os.path.join(os.path.dirname(__file__), "README.md"), encoding="utf-8"
    ).read(),
    long_description_content_type="text/markdown",
    url="https://github.com/brunomcebola/Thesis",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9.2",
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements("requirements.txt"),
    entry_points={
        "console_scripts": [
            "argos_node=argos_node.__main__:main",
        ],
    },
    cmdclass={
        "bdist_wheel": bdist_wheel,
    },
)


# Zip dist folder
shutil.make_archive("argos_node.dist", "zip", "dist")

# Clean up build artifacts
shutil.rmtree("build", ignore_errors=True)
shutil.rmtree("argos_node.egg-info", ignore_errors=True)
shutil.rmtree("dist", ignore_errors=True)
