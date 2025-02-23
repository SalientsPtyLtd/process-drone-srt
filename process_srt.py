import sys
from dataclasses import dataclass
from PIL import Image
import cv2
import re
import exif


DEFAULT_INC_SECONDS = 1
OUTPUT_DIR = './out/'


@dataclass
class ImageData:
    lat: float
    long: float
    abs_alt: float
    focal_len: float
    frame_num: int


def main(srt_path: str, mp4_path: str, inc_seconds: float):
    """Run the program.

    params:
        srt_path - the path to the srt file
        mp4_path - the path to the corresponding mp4 file
        inc_seconds - the number of seconds between frames
    """
    frame_increment = calculate_frame_increment(inc_seconds, mp4_path)
    im_data = get_meta_info(srt_path, frame_increment)
    save_images(im_data, mp4_path)


def calculate_frame_increment(seconds: float, mp4_path: str) -> int:
    """Calculates approximately the number of frames in a video, in a given
    number of seconds.
    """
    cap = cv2.VideoCapture(mp4_path)
    framerate = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    return int(framerate * seconds)


def get_meta_info(srt_f: str, inc_frames: int) -> list[ImageData]:
    """Gets meta info from a .srt file.

    Each frame has the following lines:
        frame number
        relative start time --> relative end time
        frame count
        date and time
        [attribute: value] ...
        blank line

    params:
        srt_f - the path to the srt file
        inc_frames - the number of frames between each frame

    returns: a list of ImageData objects for each necessary frame
    """

    result = []
    count = 0

    with open(srt_f, "r") as file:
        file.readline()
        file.readline()
        file.readline()
        file.readline()
        while True:
            next_line = file.readline()
            if not next_line:
                break
            attrs = read_line_attributes(next_line)

            # Add attributes to object if needed
            # Excludes frames with 0.0 latitude and longitude, as this
            # indicates incorrect GPS data
            if (
                count % inc_frames == 0
                and (float(attrs['latitude']) != 0.0
                or float(attrs['longitude']) != 0.0)
            ):
                result.append(ImageData(
                    long=float(attrs['longitude']),
                    lat=float(attrs['latitude']),
                    abs_alt=float(attrs['abs_alt']),
                    focal_len=float(attrs['focal_len']),
                    frame_num=count,
                ))

            count += 1
            file.readline()
            file.readline()
            file.readline()
            file.readline()
            file.readline()
    return result


def read_line_attributes(line: str) -> dict[str, str]:
    """Extracts attributes from a .srt files line, placing them into a
    dictionary
    """
    ret = {}
    for key, val in re.findall(r'(\w+):\s([^\s\[\]]+)', line):
        ret[key] = val
    return ret


def save_images(frames: list[ImageData], video_path: str):
    """Saves the images from a video, with metadata included.

    params:
        frames - a list of objects representing frames, with their metadata, to
                 be saved
        video_path - the path to the video to save files from
    """
    out_prefix = OUTPUT_DIR + video_path.split('/')[-1].split('.')[0] + '_'
    cap = cv2.VideoCapture(video_path)
    for frame in frames:
        print(frame)
        # Create PIL image from array
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame.frame_num)
        success, cv2_im = cap.read()
        image = Image.fromarray(cv2.cvtColor(cv2_im, cv2.COLOR_BGR2RGB))

        # Save image
        saved_name = out_prefix + str(frame.frame_num) + '.jpg'
        image.save(saved_name, 'jpeg')

        # Load saved image as exif object
        with open(saved_name, 'rb') as im_f:
            exif_image = exif.Image(im_f)

        # Add exif data
        exif_image.gps_latitude = (
            decimal_degrees_to_minutes_seconds(frame.lat))
        exif_image.gps_latitude_ref = 'N' if frame.lat > 0 else 'S'
        exif_image.gps_longitude = (
            decimal_degrees_to_minutes_seconds(frame.long))
        exif_image.gps_longitude_ref = 'E' if frame.long > 0 else 'W'
        exif_image.gps_altitude = abs(frame.abs_alt)
        exif_image.gps_altitude_ref = (exif.GpsAltitudeRef.ABOVE_SEA_LEVEL
            if frame.abs_alt > 0 else exif.GpsAltitudeRef.BELOW_SEA_LEVEL)
        exif_image.focal_length = frame.focal_len

        # Save exif data
        with open(saved_name, 'wb') as im_f:
            im_f.write(exif_image.get_file())

    cap.release()


def decimal_degrees_to_minutes_seconds(decimal: float
    ) -> tuple[float, float, float]:
    """Converts a decimal degrees to degrees, minutes, and seconds in a tuple

    params:
        decimal - the number of degrees to convert

    returns: (degrees, minutes, seconds)
    """
    # The next two lines were retrieved, and modified, from
    # https://stackoverflow.com/questions/2579535/convert-dd-decimal-degrees-to-dms-degrees-minutes-seconds-in-python
    mnt, sec = divmod(abs(decimal) * 3600, 60)
    deg, mnt = divmod(mnt, 60)
    return (deg, mnt, sec)


if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2], DEFAULT_INC_SECONDS)
    elif len(sys.argv) == 4:
        main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
    else:
        print('Usage:\n\t'
            'python3 process_srt.py <.srt file> <.mp4 file> [increment seconds]'
        )
