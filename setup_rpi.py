"""
This is the setup.py file for the Argos package. It is used to install the package using pip.
"""

from setuptools import setup, find_packages

dependencies = [
    "colorama",
    "numpy",
    "opencv-python",
    "ultralytics",
    "jsonschema",
    "PyYAML",
    "scikit-learn",
]

setup(
    name="argos",
    version="1.0.0",
    author="Bruno Cebola",
    author_email="bruno.m.cebola@gmail.com",
    description="Argos, Real-time Image Analysis for Fraud Detection",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/brunomcebola/Argos",
    packages=find_packages(),
    install_requires=dependencies,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9.2",
    entry_points={
        "console_scripts": [
            "argos=argos.argos:main",  # Assuming 'main' is your entry function in argos.py
        ],
    },
)
