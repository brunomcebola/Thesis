# Argos, Automated Real-time Guardian Observation System (`argos_master`)

`argos_master` is a Python package developed as part of the ARGOS (Automated Real-time Guardian Observation System) project. This package is designed to run as standalone application, allowing to manage and control multiple `argos_node` instances.

## Installation

### Option 1: Install from Wheel

1. **Download the Wheel File:**
   Download the `.whl` file from this [Google Drive](https://drive.google.com/drive/folders/1GuFxLusJYNchRBDVZVQ4Y0kIhF6KaKnR?usp=sharing).

2. **Install the Wheel File:**
   ```bash
   pip install path/to/argos_master-<version>.whl
   ```

### Option 2: Install from Source

1. **Clone the Repository**
   Start by cloning the repository to your local machine.

   ```bash
   git clone https://github.com/brunomcebola/Thesis.git
   cd Thesisargos/argos_master
   ```

2. **Install Dependencies**
   Last, install the required dependencies. It is recommended to create a virtual environment before installing the dependencies.
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Definition of environment variables**

   Create a configuration file `.env.argos_master` in the root directory. This file is used to set up environment variables required by `argos_node`:

   - `BASE_DIR`: The base directory where the package data is stored. If not set, the default directory is:
     - Windows: `C:\Users\<username>\AppData\Local\argos_master`
     - Linux: `/home/<username>/.local/share/argos_master`
     - MacOS: `/Users/<username>/Library/Application Support/argos_master`
   - `HOST`: The host IP address where the server will run. If not set, the default is `0.0.0.0`.
   - `PORT`: The port number where the server will run. If not set, the default is `8080`.
   - `HOT_RELOAD`: Controls if the server will automatically reload on code changes. If not set, the default is `false`.

2. **Running the package**

   If the package was installed as a wheel, you can start the node wit:

   ```bash
   argos_master
   ```

   Alternatively, you can run the package as a module:

   ```bash
   python -m argos_master
   ```

## License

This package is licensed under the Argos Restricted License. See [LICENSE](LICENSE) for more details.

For more information, visit the [project repository](https://github.com/brunomcebola/Thesis).
