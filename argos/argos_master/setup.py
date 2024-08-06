"""
This is the setup.py file for the argos_master package.
"""

import os
import shutil
from setuptools import setup, find_packages

packages = [
    "pyScss==1.4.0",
    "Flask==3.0.3",
    "flask_assets==2.1.0",
    "flask_socketio==5.3.6",
    "jsonschema==4.22.0",
    "python-dotenv==1.0.1",
    "PyYAML==6.0.1",
    "requests==2.32.3",
    "appdirs==1.4.4",
    "python-socketio[client]==5.11.3",
    "pillow==10.4.0",
]

setup(
    name="argos_master",
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
    install_requires=packages,
    entry_points={
        "console_scripts": [
            "argos_master=argos_master.__main__:main",
        ],
    },
)

# Remove the build directory
shutil.rmtree("build")

# Remove the egg-info directory
shutil.rmtree("argos_master.egg-info")
