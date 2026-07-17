"""This script will apply the position at the time the picture wa taken """

from PIL import Image
import piexif
import os
import gpx
import datetime as dt
import pytz
from pathlib import Path
from variables import *
from utils import *


def get_all_pictures() -> list:
    """
    Params:
        formats (str list): The list of picture format which have to be considered. If None, it considers everything
    
    Returns:
        A list containing the name of the files in the directory. Doesn't explore subdirs
    """
    picts_path = ""

    if PATH != "" and PATH != None:
        picts_path = PATH

    if PHOTOS_PATH != None and PHOTOS_PATH != "":
        if picts_path == "" :
            picts_path = PHOTOS_PATH
        else:
            picts_path += "\\" + PHOTOS_PATH


    if not os.path.exists(picts_path):
        print("ERROR : the path to the pictures doesn't exist")
        exit(1)

    photos = []
    for entry in os.listdir(picts_path):
        full_path = os.path.join(picts_path, entry)

        if os.path.isfile(full_path):
            _, ext = os.path.splitext(full_path)

            if PICTURE_FORMATS == None or ext in PICTURE_FORMATS:
                photos.append(entry)

    return photos

def get_all_gpxs() -> list:
    """
    Returns a list of gpx objects
    """
    gpx_path = ""

    if PATH != "" and PATH != None:
        gpx_path = PATH

    if GPXS_PATH != None and GPXS_PATH != "":
        if gpx_path == "" :
            gpx_path = GPXS_PATH
        else:
            gpx_path += "\\" + GPXS_PATH

    if not os.path.exists(gpx_path):
        print("ERROR : the path to the gpx files doesn't exist")
        exit(1)

    gpxs = []
    for entry in os.listdir(gpx_path):
        full_path = os.path.join(gpx_path, entry)

        if os.path.isfile(full_path):
            _, ext = os.path.splitext(full_path)

            if ext == ".gpx":
                gpxs.append(gpx.read_gpx(full_path))

    return gpxs

def get_all_gpxs_files() -> list:
    """
    Returns a list of the name of the files
    """
    gpx_path = ""

    if PATH != "" and PATH != None:
        gpx_path = PATH

    if GPXS_PATH != None and GPXS_PATH != "":
        if gpx_path == "" :
            gpx_path = GPXS_PATH
        else:
            gpx_path += "\\" + GPXS_PATH

    if not os.path.exists(gpx_path):
        print("ERROR : the path to the gpx files doesn't exist")
        exit(1)

    gpxs = []
    for entry in os.listdir(gpx_path):
        full_path = os.path.join(gpx_path, entry)

        if os.path.isfile(full_path):
            _, ext = os.path.splitext(full_path)

            if ext == ".gpx":
                gpxs.append(full_path)

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

def import_from_trace():
    """
    Process the pictures in the pictures path, using the gpx files.
    """
    gpx_lst = get_all_gpxs()

    if len(gpx_lst) == 0:
        print("ERROR : no gpx files found in the specified directory with the good format")
        exit(1)

    pictures = get_all_pictures()

    if len(pictures) == 0:
        print("ERROR : no photos found in the specified directory with the good format")
        exit(1)

    pos_lst = get_pos(gpx_lst)

    for picture in pictures:
        pict_path = get_pict_path(picture)
        img = Image.open(pict_path)

        if "exif" in img.info:
            exif_dict = piexif.load(img.info["exif"])
            img.close()
        else:
            # TODO make it work in this case too
            print(f"ERROR : the picture {picture} has no exif data ! I will ignore it.")
            img.close()
            process_failed_pictures(picture)
            continue
    
        pos = get_closest_pos(pos_lst, get_pict_time(exif_dict))
        picture_add_position(picture, pos)


if __name__ == "__main__":
    #print(get_all_pictures(None))
    import_from_trace()

