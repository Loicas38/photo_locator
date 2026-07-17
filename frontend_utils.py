from PIL import Image
from variables import *
import os
import piexif
import pandas as pd


def convert_lat_long(pos):
    """
    to convert the pos extraceted from exif
    """
    lat = pos[0][0]
    long = pos[1][0]

    return (lat[0], long[0])


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
        "Longitude": []
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
                    data["Latitude"].append(str(lat))
                    data["Longitude"].append(str(long))
                    #data["thumbnail"].append(exif_dict.get("thumbnail"))
                else:
                    data["Latitude"].append("NaN")
                    data["Longitude"].append("NaN")
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


if __name__ =="__main__":
    print(get_picts_details())