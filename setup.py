"""
This is the setup.py file for the Argos package. It is used to install the package using pip.
"""

import platform
from setuptools import setup, find_packages

dependencies = []

# Add conditional dependency for pyrealsense2, only if not running on Raspberry Pi
# Raspberry Pis typically return 'armv7l', 'armv6l', or 'aarch64' for platform.machine() on Linux,
# depending on the model and OS version. Adjust the condition as needed.
if not platform.machine() in ('armv7l', 'armv6l', 'aarch64'):
    dependencies.append('pyrealsense2')

# Assuming the .so files for Raspberry Pi are in the 'libs' directory within your 'argos' package
package_data_specific = {}
if platform.machine() in ('armv7l', 'armv6l', 'aarch64'):
    package_data_specific['argos'] = ['libs/*.so']

setup(
    name="argos",
    version="0.1.0",
    author="Bruno Cebola",
    author_email="bruno.m.cebola@gmail.com",
    description="Argos, Real-time Image Analysis for Fraud Detection",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/brunomcebola/Argos",
    packages=find_packages(),
    include_package_data=True,
    package_data=package_data_specific,
    install_requires=dependencies,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9.2",
    entry_points={
        "console_scripts": [
            "argos=argos.__main__:main",  # Assuming 'main' is your entry function in argos.py
        ],
    },
)
