"""
This is the setup.py file for the Argos package. It is used to install the package using pip.
"""

import os
from setuptools import setup, find_packages

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
    packages=find_packages(),
    install_requires=[
        "Flask==3.0.3",
        "flask_socketio==5.3.6",
        "jsonschema==4.23.0",
        "numpy==2.0.1",
        "python-dotenv==1.0.1",
        "PyYAML==6.0.1",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9.2",
    entry_points={
        "console_scripts": [
            "argos master=argos_node.__main__:main",
        ],
    },
)
