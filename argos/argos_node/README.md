# Argos, Automated Real-time Guardian Observation System (`argos_node`)

`argos_node` is a Python package developed as part of the ARGOS (Automated Real-time Guardian Observation System) project. This package is designed to run as standalone application, allowing to capture and stream video from intel realsense cameras.

## Installation

### Option 1: Install from Wheel

1. **Download the Wheel File:**
   Download the `.whl` file from this [Google Drive](https://drive.google.com/drive/folders/1GuFxLusJYNchRBDVZVQ4Y0kIhF6KaKnR?usp=sharing).

2. **Install the Wheel File:**
   ```bash
   pip install path/to/argos_node-<version>.whl
   ```

### Option 2: Install from Source

1. **Clone the Repository**
   Start by cloning the repository to your local machine.

   ```bash
   git clone https://github.com/brunomcebola/Thesis.git
   cd Thesis/argos/argos_node
   ```

2. **(RPi only) Shared Object (.so) files**
   For running `argos_node` on a Raspberry Pi, specific shared object (.so) files are required and must be placed at the root directory. This files are available for download in this [Google Drive](https://drive.google.com/drive/folders/1fKuF8BSmQzeL60sy2dDHtUZFuy2_mxPq?usp=sharing). Alternatively, you can build the shared object files by following the instructions in the [librealsense GitHub repository](https://github.com/IntelRealSense/librealsense/blob/master/wrappers/python/readme.md).

3. **Install Dependencies**
   Last, install the required dependencies. It is recommended to create a virtual environment before installing the dependencies.
   ```bash
   pip install -r requirements.txt
   ```
   **Note:** if installing in a machine other than Raspberry Pi, the first line of the `requirements.txt` file must be uncommented, in order to install the correct version of the `pyrealsense2` package.

## Usage

1. **Definition of environment variables**

   Create a configuration file `.env.argos_node` in the root directory. This file is used to set up environment variables required by `argos_node`:

   - `BASE_DIR`: The base directory where the package data is stored. If not set, the default directory is:
     - Windows: `C:\Users\<username>\AppData\Local\argos_node`
     - Linux: `/home/<username>/.local/share/argos_node`
     - MacOS: `/Users/<username>/Library/Application Support/argos_node`
   - `HOST`: The host IP address where the server will run. If not set, the default is `0.0.0.0`.
   - `PORT`: The port number where the server will run. If not set, the default is `5000`.
   - `HOT_RELOAD`: Controls if the server will automatically reload on code changes. If not set, the default is `false`.

2. **Configuration of the cameras**

   Only the cameras that have a configuration file in the `BASE_DIR/cameras/` directory will be used. A configuration file named `<serial_number>.yaml` is automatically created for each connected camera when the package is run, if it does not exist yet. The configuration file should be as follows:

   ```yaml
   stream_configs:
     - type: color
       format: bgr8
       resolution: x640_y480
       fps: fps_30
     - type: depth
       format: z16
       resolution: x640_y480
       fps: fps_30
   alignment: color
   ```

   There can be multiple streams defined in the `stream_configs` list. Each config must have the following fields:

   - `type`: The type of the stream. The available options can be found in the `StreamType` class in the `realsense.py` file or listed in the console using the `--realsense-types` argument.
   - `format`: The format of the stream. The available options can be found in the `StreamFormat` class in the `realsense.py` file or listed in the console using the `--realsense-formats` argument.
   - `resolution`: The resolution of the stream. The available options can be found in the `StreamResolution` class in the `realsense.py` file or listed in the console using the `--realsense-resolutions` argument.
   - `fps`: The frames per second of the stream. The available options can be found in the `StreamFps` class in the `realsense.py` file or listed in the console using the `--realsense-fps` argument.

   The `alignment` field defines the stream that will be used as the reference for the alignment of the other streams. It must allways be one of the streams defined in the `stream_configs` list.

3. **Running the package**

   If the package was installed as a wheel, you can start the node wit:

   ```bash
   argos_node
   ```

   Alternatively, you can run the package as a module:

   ```bash
   python -m argos_node
   ```

## License

This package is licensed under the Argos Restricted License. See [LICENSE](LICENSE) for more details.

For more information, visit the [project repository](https://github.com/brunomcebola/Thesis).
