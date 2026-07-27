import os 
from pathlib import Path
import piexif
import pytz
import datetime as dt
import streamlit as st
import io
import zipfile
from utils import *
#from pos_management import *


def process_failed_pictures(picture: str):
    """
    Renames the pictures whch have not been processed
    """
    path = ""

    if st.session_state["PATH"] != "" and st.session_state["PATH"] != None:
        path = st.session_state["PATH"] + "\\"

    path += st.session_state["FAILED_PATH"] + "\\" + picture

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    p = Path(get_pict_path(picture))
    p.rename(path)

def get_pict_time(exif_dict: dict) -> dt:
    """
    Returns a datetime object containing the time at which the picture was taken, using the data 
    in the variables.py file
    """
    if exif_dict["Exif"].get(piexif.ExifIFD.DateTimeOriginal) == None:
        return None

    time_format = "%Y:%m:%d %H:%M:%S"
    pict_time = dt.datetime.strptime(exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal].decode(), time_format)
    pict_time = pict_time - get_time_advance_dt()
    # print(f"picture {picture} at {pict_time}")

    # time zone gestion
    # TODO : ask the user which time zone to use
    tz = pytz.timezone(st.session_state["CAMERA_TIMEZONE"])
    pict_time = tz.localize(pict_time)

    return pict_time

def get_pict_path(picture: str):
    pict_path = ""

    if st.session_state["PATH"] != None and st.session_state["PATH"] != "":
        pict_path = st.session_state["PATH"] + "\\"

    if st.session_state["PHOTOS_PATH"] != None and st.session_state["PHOTOS_PATH"] != "":
        pict_path += st.session_state["PHOTOS_PATH"] + "\\"

    pict_path += picture 

    return pict_path

def get_all_pictures() -> list:
    """
    Params:
        formats (str list): The list of picture format which have to be considered. If None, it considers everything
    
    Returns:
        A list containing the name of the files in the directory. Doesn't explore subdirs
    """
    picts_path = ""

    if st.session_state["PATH"] != "" and st.session_state["PATH"] != None:
        picts_path = st.session_state["PATH"]

    if st.session_state["PHOTOS_PATH"] != None and st.session_state["PHOTOS_PATH"] != "":
        if picts_path == "" :
            picts_path = st.session_state["PHOTOS_PATH"]
        else:
            picts_path += "\\" + st.session_state["PHOTOS_PATH"]


    if not os.path.exists(picts_path):
        print("ERROR : the path to the pictures doesn't exist")
        exit(1)

    photos = []
    for entry in os.listdir(picts_path):
        full_path = os.path.join(picts_path, entry)

        if os.path.isfile(full_path):
            _, ext = os.path.splitext(full_path)

            if st.session_state["PICTURE_FORMATS"] == None or ext in st.session_state["PICTURE_FORMATS"]:
                photos.append(entry)

    return photos


def get_failed_pict_path(picture: str):
    pict_path = ""

    if st.session_state["PATH"] != None and st.session_state["PATH"] != "":
        pict_path = st.session_state["PATH"] + "\\"

    if st.session_state["FAILED_PATH"] != None and st.session_state["FAILED_PATH"] != "":
        pict_path += st.session_state["FAILED_PATH"] + "\\"

    pict_path += picture 

    return pict_path



def get_picts_details() -> dict:
    """
    Returns a dict containing lists with the data of the pictures in PATH\\PHOTOS_PATH
    """

    picts_path = ""

    if st.session_state["PATH"] != "" and st.session_state["PATH"] != None:
        picts_path = st.session_state["PATH"]

    if st.session_state["PHOTOS_PATH"] != None and st.session_state["PHOTOS_PATH"] != "":
        if picts_path == "" :
            picts_path = st.session_state["PHOTOS_PATH"]
        else:
            picts_path += "\\" + st.session_state["PHOTOS_PATH"]


    if not os.path.exists(picts_path):
        print("ERROR : the path to the pictures doesn't exist")
        return None

    data = {
        "files": [],
        "Latitude": [],
        "Longitude": [],
        "Time": []
        #"thumbnail": []
    }


    for entry in os.listdir(picts_path):
        full_path = os.path.join(picts_path, entry)

        if os.path.isfile(full_path):
            _, ext = os.path.splitext(full_path)

            if st.session_state["PICTURE_FORMATS"] == None or ext in st.session_state["PICTURE_FORMATS"]:
                # this is a picture with the good extension
                data["files"].append(entry)

                exif_dict = piexif.load(full_path)

                if True:
                    # TODO : check what happens when there is no exif
                    lat, long = convert_lat_long((exif_dict.get("GPS").get(piexif.GPSIFD.GPSLatitude), exif_dict.get("GPS").get(piexif.GPSIFD.GPSLongitude)))
                    data["Latitude"].append(lat)
                    data["Longitude"].append(long)
                    data["Time"].append(get_pict_time(exif_dict))
                    #data["thumbnail"].append(exif_dict.get("thumbnail"))
                else:
                    data["Latitude"].append(None)
                    data["Longitude"].append(None)
                    data["Time"].append(None)
                    #data["thumbnail"].append(None)

    
    return data

def get_failed_pictures():
    """
    Returns a dict containing lists with the data of the pictures in PATH\\PHOTOS_PATH
    """

    picts_path = ""

    if st.session_state["PATH"] != "" and st.session_state["PATH"] != None:
        picts_path = st.session_state["PATH"]

    if st.session_state["FAILED_PATH"] != None and st.session_state["FAILED_PATH"] != "":
        if picts_path == "" :
            picts_path = st.session_state["FAILED_PATH"]
        else:
            picts_path += "\\" + st.session_state["FAILED_PATH"]


    if not os.path.exists(picts_path):
        print("ERROR : the path to the pictures doesn't exist")
        return None

    data = {
        "Pictures": []
    }


    for entry in os.listdir(picts_path):
        full_path = os.path.join(picts_path, entry)

        if os.path.isfile(full_path):
            _, ext = os.path.splitext(full_path)

            if st.session_state["PICTURE_FORMATS"] == None or ext in st.session_state["PICTURE_FORMATS"]:
                # this is a picture with the good extension
                data["Pictures"].append(entry)
    
    return data

def delete_picture(picture: str):
    """
    Delets the given picture. `picture` is the filename of the picture to delete
    """
    path = get_pict_path(picture)

    os.remove(path)

def delete_all_pictures():
    """
    Deletes all pictures
    """

    pictures = get_all_pictures()

    for pict in pictures:
        delete_picture(pict)

def delete_failed_picture(picture: str):
    """
    Deletes the picture in the path of the ones which failed
    """

    path = get_failed_pict_path(picture)
    os.remove(path)

def delete_all_failed_pictures():
    picts = get_failed_pictures()
    
    for pict in picts:
        delete_failed_picture(pict)

def get_zip_successful_data():
    """
    Returns the content of a zip with the pictures in the PHOTO_PATH directory
    """
    buf = io.BytesIO()
    pictures = get_all_pictures()

    with zipfile.ZipFile(buf, "x") as im_zip:
        for pict in pictures:
            im_zip.write(get_pict_path(pict))

    return buf

def get_zip_failed_data():
    """
    Returns the content of a zip with the pictures in the PHOTO_PATH directory
    """
    buf = io.BytesIO()
    pictures = get_failed_pictures()

    with zipfile.ZipFile(buf, "x") as im_zip:
        for pict in pictures:
            im_zip.write(get_failed_pict_path(pict))

    return buf
