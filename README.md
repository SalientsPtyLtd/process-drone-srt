
# `.mp4` With `.srt` To `.jpeg` With EXIF Metadata

This is a tool which, given an `.mp4` and a corresponding DJI `.srt` file, will
output a series of `.jpeg` files, with some metadata added to the EXIF data. The
DJI `.srt` files are output by DJI drones, and include GPS and camera
information for each frame. The metadata added is that which is required for
building models using the Agisoft Metashape software. This includes:

* Latitude
* Longitude
* Altitude
* Focal Length

Other pieces of metadata are ignored, as they are not necessary.

## Installation

Before following these steps, Python 3 and Pip must be installed.

1. Clone this repository, and change directory into it.
2. Create a Python virtual environment using `python3 -m venv venv`.
3. Activate the virtual environment. This will depend on your platform:
  * **Windows:** Run `.\venv\bin\activate`.
  * **Linux/UNIX:** Run `source ./venv/bin/activate`.
4. Install dependencies for the virtual environment, using
`python3 -m pip install -r requirements.txt`.

## Usage

Before running the code, it is necessary to activate the virtual environment.
To do this, follow step 3 of the installation steps above.

Run the program using `python3 process_srt.py <.srt file> <.mp4 file>`.
