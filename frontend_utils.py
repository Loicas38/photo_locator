from PIL import Image
from variables import *
import os
import piexif
import pandas as pd
from utils import *
import io
import zipfile

def convert_lat_long(pos):
    """
    to convert the pos extraceted from exif
    """
    if pos == None or pos[0] == None:
        return None, None

    lat = pos[0][0][0] / pos[0][0][1] + pos[0][1][0] / (60 * pos[0][1][1]) + pos[0][2][0] / (3600 * pos[0][2][1])
    long = pos[1][0][0] / pos[1][0][1] + pos[1][1][0] / (60 * pos[1][1][1]) + pos[1][2][0] / (3600 * pos[1][2][1])

    return (lat, long)

def get_picts_details() -> dict:
    """
    Returns a dict containing lists with the data of the pictures in PATH\PHOTOS_PATH
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

            if PICTURE_FORMATS == None or ext in PICTURE_FORMATS:
                # this is a picture with the good extension
                data["files"].append(entry)

                img = Image.open(full_path)

                if "exif" in img.info:
                    exif_dict = piexif.load(img.info["exif"])
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

                img.close()
    
    return data

def get_failed_pictures():
    """
    Returns a dict containing lists with the data of the pictures in PATH\PHOTOS_PATH
    """

    picts_path = ""

    if PATH != "" and PATH != None:
        picts_path = PATH

    if FAILED_PATH != None and FAILED_PATH != "":
        if picts_path == "" :
            picts_path = FAILED_PATH
        else:
            picts_path += "\\" + FAILED_PATH


    if not os.path.exists(picts_path):
        print("ERROR : the path to the pictures doesn't exist")
        exit(1)

    data = {
        "Pictures": []
    }


    for entry in os.listdir(picts_path):
        full_path = os.path.join(picts_path, entry)

        if os.path.isfile(full_path):
            _, ext = os.path.splitext(full_path)

            if PICTURE_FORMATS == None or ext in PICTURE_FORMATS:
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

def get_gpx_path(gpx_f: str) -> str:
    """
    returns the path towards the gpx file specified
    """

    path = ""

    if PATH != "" and PATH != None:
        path += PATH + "\\"

    if GPXS_PATH != None and GPXS_PATH != "":
        path += GPXS_PATH + "\\"

    path += gpx_f

    return path

def delete_gpx(g: str):
    path = get_gpx_path(g)
    os.remove(path)

if __name__ =="__main__":
    data = get_picts_details()
    p = pd.DataFrame(data)
    p = pd.DataFrame(data).dropna(subset=["Latitude", "Longitude"])
    print(len(p["Longitude"]))