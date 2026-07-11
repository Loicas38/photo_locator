"""This script will apply the position at the time the picture wa taken """

from PIL import Image
import piexif
import os
import gpx
import datetime as dt
import pytz
from math import modf, floor

PHOTOS_PATH = "test"
GPX_FILE = "activity.gpx"
# the number of seconds of margin for th closest position
# so, if a position exists at less than EPSILON seconds of its taken time, it will be 
# considered valid, otherwise not. If None, there is no limit
EPSILON = dt.timedelta(minutes=1)
# the minutes the camera has on the real time
TIME_ADVANCE = dt.timedelta(minutes=7)

CAMERA_TIMEZONE = "Europe/Paris"


def get_all_pictures(formats: list) -> list:
    """
    Params:
        formats (str list): The list of picture format which have to be considered. If None, it considers everything
    
    Returns:
        A list containing the name of the files in the directory. Doesn't explore subdirs
    """

    photos = []
    for entry in os.listdir(PHOTOS_PATH):
        full_path = os.path.join(PHOTOS_PATH, entry)

        if os.path.isfile(full_path):
            _, ext = os.path.splitext(full_path)

            if formats == None or ext in formats:
                photos.append(full_path)

    return photos

def comparing_fun(dic: dict) -> int:
    """ comparing function for the sort of the positions """
    return dic["time"]


def get_closest_pos(positions: list, time: dt) -> dict:
    """ returns the pos which is the closest from the time at which the picture was taken. 
    If there is no existing position satisfying EPSILON, it will return None.
    The positions must be sorted by ascendent time
    
    TODO : implement dichotomic search to speed up
    TODO : check if the picture was taken in the interrval, not before or after
    """
    for i, d in enumerate(positions):
        # the searched time is before since the list is sorted
        if d["time"] > time:
            gap1 = time - positions[i - 1]["time"]
            gap2 = d["time"] - time

            if gap1 < gap2:
                if gap1 < EPSILON:
                    return positions[i - 1]
                else:
                    return None
            else :
                if gap2 < EPSILON:
                    return d
                else:
                    return None

    print(positions[0])    
    print(positions[-1])


def main():
    if not os.path.exists(GPX_FILE):
        print("ERROR : the gpx file doesn't exist")
        exit(1)

    gpxf = gpx.read_gpx(GPX_FILE)

    pictures = get_all_pictures(None)

    if len(pictures) == 0:
        print("ERROR : no photos found in the specified directory with the good format")
        exit(1)

    # creating the list of positions
    if len(gpxf.trk) != 1:
        print("ERROR : there is more than one track in the pgx file !")
        exit(1)

    positions = []
    
    if len(gpxf.trk) > 1:
        print("There are multiple tracks in the gpx file. I will consider the points in all of them.")
    
    for track in gpxf.trk:
        # Iterate over track segments and points
        for track_segment in track.trkseg:
            for track_point in track_segment.trkpt:
                positions.append({
                    "latitude": track_point.lat,
                    "longitude": track_point.lon,
                    "time": track_point.time
                })

    positions.sort(key = comparing_fun)


    for picture in pictures:
        img = Image.open(picture)

        if "exif" in img.info:
            exif_dict = piexif.load(img.info["exif"])
        else:
            # TODO make it work in this case too
            print(f"ERROR : he picture {picture} has no exif data ! I will ignore it.")
            continue

        exif_dict = piexif.load(picture)

        time_format = "%Y:%m:%d %H:%M:%S"
        pict_time = dt.datetime.strptime(exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal].decode(), time_format)
        pict_time = pict_time - TIME_ADVANCE
        print(pict_time)

        # time zone gestion
        # TODO : ask the user which time zone to use
        tz = pytz.timezone(CAMERA_TIMEZONE)
        pict_time = tz.localize(pict_time)

        pos = get_closest_pos(positions, pict_time)
        
        # converting to degree, minute, seconds
        frac, degree = modf(pos["longitude"])
        frac, minutes = modf(frac * 60)
        seconds = floor(frac * 60) # TODO : should be decimal seconds, chekc if this is ok

        lon_tuple = ((int(degree), 1), (int(minutes), 1), (int(seconds * 100), 100))
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = lon_tuple
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = "E" if pos["longitude"] >= 0 else "W"

        frac, degree = modf(pos["latitude"])
        frac, minutes = modf(frac * 60)
        seconds = floor(frac * 60) # TODO : should be decimal seconds, chekc if this is ok

        lat_tuple = ((int(degree), 1), (int(minutes), 1), (int(seconds * 100), 100))
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = lat_tuple
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = "N" if pos["latitude"] >= 0 else "S"

        exif_bytes = piexif.dump(exif_dict)
        img.save(picture, exif=exif_bytes, quality="keep")
    

    


if __name__ == "__main__":
    print(get_all_pictures(None))
    main()

