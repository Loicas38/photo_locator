from variables import *
import os 
from pathlib import Path
from PIL import Image
import piexif
import pytz
import datetime as dt

def process_failed_pictures(picture: str):
    """
    Renames the pictures whch have not been processed
    """
    path = ""

    if PATH != "" and PATH != None:
        path = PATH + "\\"

    path += "failed\\" + picture

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    p = Path(get_pict_path(picture))
    p.rename(path)

def get_pict_time(exif_dict: dict) -> dt:
    """
    Returns a datetime object containing the time at which the picture was taken, using the data 
    in the variables.py file
    """
    time_format = "%Y:%m:%d %H:%M:%S"
    pict_time = dt.datetime.strptime(exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal].decode(), time_format)
    pict_time = pict_time - TIME_ADVANCE
    # print(f"picture {picture} at {pict_time}")

    # time zone gestion
    # TODO : ask the user which time zone to use
    tz = pytz.timezone(CAMERA_TIMEZONE)
    pict_time = tz.localize(pict_time)

    return pict_time

def get_pict_path(picture: str):
    pict_path = ""

    if PATH != None and PATH != "":
        pict_path = PATH + "\\"

    if PHOTOS_PATH != None and PHOTOS_PATH != "":
        pict_path += PHOTOS_PATH + "\\"

    pict_path += picture 

    return pict_path

def picture_add_position(picture: str, pos: dict) -> bool:
    """
    Adds the location to the picture.

    Params:
        picture (str): The name of the picture to process
        pos (dict): A dict containing the keys 'lattitude' and 'longitude' which will be used. The must be decimal.

    Returns:
        A boolean, true if it succedded, false otherwise
    """
    pict_path = get_pict_path(picture)

    img = Image.open(pict_path)

    if "exif" in img.info:
        exif_dict = piexif.load(img.info["exif"])
    else:
        # TODO make it work in this case too
        print(f"ERROR : the picture {picture} has no exif data ! I will ignore it.")
        img.close()
        process_failed_pictures(picture)
        return

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
    img.save(pict_path, exif=exif_bytes, quality="keep")

def remove_position(picture: str):
    """
    Removes the location of picture
    """

    pict_path = get_pict_path(picture)

    img = Image.open(pict_path)

    if "exif" in img.info:
        exif_dict = piexif.load(img.info["exif"])
    else:
        return

    exif_dict.pop("GPS", None)

    exif_bytes = piexif.dump(exif_dict)
    img.save(pict_path, exif=exif_bytes, quality="keep")



if __name__ == "__main__":
    remove_position("DSC_2668.JPG")