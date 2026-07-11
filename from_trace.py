"""This script will apply the position at the time the picture wa taken """

from PIL import Image
import piexif
import os
import gpx
import datetime as dt
import pytz
from pathlib import Path

PHOTOS_PATH = "pictures"
GPXS_PATH = "gpxs"
# the number of seconds of margin for th closest position
# so, if a position exists at less than EPSILON seconds of its taken time, it will be 
# considered valid, otherwise not. If None, there is no limit
EPSILON = dt.timedelta(minutes=1)
# the minutes the camera has on the real time
TIME_ADVANCE = dt.timedelta(minutes=6, seconds=13)

CAMERA_TIMEZONE = "Europe/Paris"


def get_all_pictures(formats: list) -> list:
    """
    Params:
        formats (str list): The list of picture format which have to be considered. If None, it considers everything
    
    Returns:
        A list containing the name of the files in the directory. Doesn't explore subdirs
    """
    if not os.path.exists(GPXS_PATH):
        print("ERROR : the path to the pictures doesn't exist")
        exit(1)

    photos = []
    for entry in os.listdir(PHOTOS_PATH):
        full_path = os.path.join(PHOTOS_PATH, entry)

        if os.path.isfile(full_path):
            _, ext = os.path.splitext(full_path)

            if formats == None or ext in formats:
                photos.append(full_path)

    return photos

def get_all_gpxs() -> list:
    """
    Returns a list of gpx objects
    """
    if not os.path.exists(GPXS_PATH):
        print("ERROR : the path to the gpx files doesn't exist")
        exit(1)

    gpxs = []
    for entry in os.listdir(GPXS_PATH):
        full_path = os.path.join(GPXS_PATH, entry)

        if os.path.isfile(full_path):
            _, ext = os.path.splitext(full_path)

            if ext == ".gpx":
                gpxs.append(gpx.read_gpx(full_path))

    return gpxs

def pos_comparing_fun(dic: dict) -> dt:
    """ comparing function for the sort of the positions """
    return dic["time"]

def pos_lst_comparing_fun(lst: list) -> dt:
    """
    Params:
        lst (dict list): A sorted list of position in dict shape.

    Returns:
        The date of the first element of the list (so the smallest).
    """
    return lst[0]["time"]

def get_closest_pos(positions: list, time: dt) -> dict:
    """ returns the pos which is the closest from the time at which the picture was taken.
    It must be within one of the lists contained in positions, otherwise it will return None.
    If there is no existing position satisfying EPSILON, it will return None.
    The positions must be sorted by ascendent time
    
    TODO : implement dichotomic search to speed up
    TODO : check if the picture was taken in the interrval, not before or after
    """
    current_best = None
    best_delta = dt.timedelta(seconds=0)

    for pos_lst in positions:
        #  the time is before the first element, but everything is sorted, so it can't be find
        if pos_lst[0]["time"] > time:
            break
        
        for i, d in enumerate(pos_lst):
            # the searched time is before since the list is sorted
            if d["time"] > time:

                gap1 = time - pos_lst[i - 1]["time"]
                gap2 = d["time"] - time

                if gap1 < gap2:
                    if gap1 < EPSILON:
                        if current_best == None or gap1 < best_delta:
                            current_best = pos_lst[i - 1]
                            best_delta = gap1

                else :
                    if gap2 < EPSILON:
                        if current_best == None or gap2 < best_delta:
                            current_best = d
                            best_delta = gap2

                break

    return current_best

def get_pos(gpxs : list) -> list:
    """
    Extracts gpx files content into gpx objects to make a list with

    Params:
        gpxs (gpx list): the list of gpx files to consider

    Returns:
        A list of list, each one containing the positions of one of the gpx file. 
        Each list is sorted by ascendant time, and the lists are sorted by the time of the first point
    """
    pos_lst = []

    for g in gpxs:
        if len(g.trk) > 1:
            print("There are multiple tracks in a gpx file. I will consider the points in all of them.")
        elif len(g.trk) == 0:
            print("One of the gpx files doesn't contain any track. I will ignore it.")
            continue

        cur_pos = []

        for track in g.trk:
            # Iterate over track segments and points
            for track_segment in track.trkseg:
                for track_point in track_segment.trkpt:
                    cur_pos.append({
                        "latitude": track_point.lat,
                        "longitude": track_point.lon,
                        "time": track_point.time
                    })

        cur_pos.sort(key = pos_comparing_fun)
        pos_lst.append(cur_pos)

    pos_lst.sort(key = pos_lst_comparing_fun)
    return pos_lst

def process_failed_pictures(picture: str):
    """
    Renames the pictures whch have not been processed
    """
    path = "failed" + picture

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    p = Path(picture)
    p.rename(path)

def picture_add_position(picture: str, pos_lst: list):
    """
    Adds the location to the picture.

    Params:
        picture (str): The name of the picture to process
        pos_lst (list): A list of pos list, both kind of lists have to be sorted by time.
    """
    img = Image.open(picture)

    if "exif" in img.info:
        exif_dict = piexif.load(img.info["exif"])
    else:
        # TODO make it work in this case too
        print(f"ERROR : the picture {picture} has no exif data ! I will ignore it.")
        img.close()
        process_failed_pictures(picture)
        return

    exif_dict = piexif.load(picture)

    time_format = "%Y:%m:%d %H:%M:%S"
    pict_time = dt.datetime.strptime(exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal].decode(), time_format)
    pict_time = pict_time - TIME_ADVANCE
    # print(f"picture {picture} at {pict_time}")

    # time zone gestion
    # TODO : ask the user which time zone to use
    tz = pytz.timezone(CAMERA_TIMEZONE)
    pict_time = tz.localize(pict_time)

    pos = get_closest_pos(pos_lst, pict_time)
    if pos == None:
        print(f"No location found for '{picture}', I will ignore it.")
        img.close()
        process_failed_pictures(picture)
        return
    
    # --- Conversion pour la LATITUDE ---
    lat_val = pos["latitude"]
    lat_ref = b"N" if lat_val >= 0 else b"S" # Notez le 'b' devant la chaîne

    abs_lat = abs(lat_val)
    lat_deg = int(abs_lat)
    lat_min_float = (abs_lat - lat_deg) * 60
    lat_min = int(lat_min_float)
    lat_sec = int(round((lat_min_float - lat_min) * 60 * 100)) # Stocké x100 pour garder 2 décimales

    # Tuple final : ((degrés, 1), (minutes, 1), (secondes*100, 100))
    lat_tuple = ((lat_deg, 1), (lat_min, 1), (lat_sec, 100))


    # --- Conversion pour la LONGITUDE ---
    lon_val = pos["longitude"]
    lon_ref = b"E" if lon_val >= 0 else b"W" # Notez le 'b' devant la chaîne

    abs_lon = abs(lon_val)
    lon_deg = int(abs_lon)
    lon_min_float = (abs_lon - lon_deg) * 60
    lon_min = int(lon_min_float)
    lon_sec = int(round((lon_min_float - lon_min) * 60 * 100))

    lon_tuple = ((lon_deg, 1), (lon_min, 1), (lon_sec, 100))


    # --- Application dans le dictionnaire piexif ---
    # exif_dict["GPS"][piexif.GPSIFD.GPSVersionID] = (2, 2, 0, 0) # Optionnel mais recommandé
    exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = lat_ref
    exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = lat_tuple
    exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = lon_ref
    exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = lon_tuple

    exif_bytes = piexif.dump(exif_dict)
    img.save(picture, exif=exif_bytes, quality="keep")

def main():
    gpx_lst = get_all_gpxs()

    if len(gpx_lst) == 0:
        print("ERROR : no gpx files found in the specified directory with the good format")
        exit(1)

    pictures = get_all_pictures(None)

    if len(pictures) == 0:
        print("ERROR : no photos found in the specified directory with the good format")
        exit(1)

    pos_lst = get_pos(gpx_lst)

    for picture in pictures:
        picture_add_position(picture, pos_lst)



if __name__ == "__main__":
    #print(get_all_pictures(None))
    main()

