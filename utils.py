import os 
from pathlib import Path
from PIL import Image
import piexif
import pytz
import datetime as dt
import json
import streamlit as st
import io
import zipfile

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

def get_failed_pict_path(picture: str):
    pict_path = ""

    if st.session_state["PATH"] != None and st.session_state["PATH"] != "":
        pict_path = st.session_state["PATH"] + "\\"

    if st.session_state["FAILED_PATH"] != None and st.session_state["FAILED_PATH"] != "":
        pict_path += st.session_state["FAILED_PATH"] + "\\"

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

    exif_dict= {
            "GPS": {}
        }

    if "exif" in img.info:
        exif_dict = piexif.load(img.info["exif"])
    """else:
        pass
        
        # TODO make it work in this case too
        print(f"ERROR : the picture {picture} has no exif data ! I will ignore it.")
        img.close()
        process_failed_pictures(picture)
        return"""

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

    return True

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

def store_settings():
    """
    Saves the variables of variables.py in settings.json
    """

    dic = {
        "PATH": st.session_state.PATH,
        "PHOTOS_PATH": st.session_state.PHOTOS_PATH,
        "FAILED_PATH": st.session_state.FAILED_PATH,
        "SUCCESS_PATH": st.session_state.SUCCESS_PATH,
        "GPXS_PATH": st.session_state.GPXS_PATH,

        "EPSILON_days": st.session_state.EPSILON_days,
        "EPSILON_hours": st.session_state.EPSILON_hours,
        "EPSILON_minutes": st.session_state.EPSILON_minutes,
        "EPSILON_seconds": st.session_state.EPSILON_seconds,

        "TIME_ADVANCE_days" : st.session_state.TIME_ADVANCE_days,
        "TIME_ADVANCE_hours" : st.session_state.TIME_ADVANCE_hours,
        "TIME_ADVANCE_minutes" : st.session_state.TIME_ADVANCE_minutes,
        "TIME_ADVANCE_seconds" : st.session_state.TIME_ADVANCE_seconds,

        "CAMERA_TIMEZONE": st.session_state.CAMERA_TIMEZONE,

        "PICTURE_FORMATS": st.session_state.PICTURE_FORMATS
    }

    with open("settings.json", "w") as f:
        json.dump(dic, f, indent=4)



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

def get_gpx_path(gpx_f: str) -> str:
    """
    returns the path towards the gpx file specified
    """

    path = ""

    if st.session_state["PATH"] != "" and st.session_state["PATH"] != None:
        path += st.session_state["PATH"] + "\\"

    if st.session_state["GPXS_PATH"] != None and st.session_state["GPXS_PATH"] != "":
        path += st.session_state["GPXS_PATH"] + "\\"

    path += gpx_f

    return path

def delete_gpx(g: str):
    path = get_gpx_path(g)
    os.remove(path)

def get_time_advance_dt() -> dt:
    return dt.timedelta(
            seconds=st.session_state.TIME_ADVANCE_seconds,
            minutes=st.session_state.TIME_ADVANCE_minutes,
            hours=st.session_state.TIME_ADVANCE_hours,
            days=st.session_state.TIME_ADVANCE_days
        )

def get_epsilon_dt() -> dt:
    return dt.timedelta(
            seconds=st.session_state.EPSILON_seconds,
            minutes=st.session_state.EPSILON_minutes,
            hours=st.session_state.EPSILON_hours,
            days=st.session_state.EPSILON_days
        )

def load_settings():
    if "settings_loaded" not in st.session_state:
    
        with open("settings.json", "r") as f:
            saved_settings = json.load(f)

        
        for key, value in saved_settings.items():
            st.session_state[key] = value
            
        st.session_state["settings_loaded"] = True


if __name__ == "__main__":
    picture="DSC_2668.JPG"
    pict_path = get_pict_path(picture)

    img = Image.open(pict_path)

    if "exif" in img.info:
        exif_dict = piexif.load(img.info["exif"])
        print(exif_dict.keys())
        print(exif_dict["GPS"].keys())
    else:
        # TODO make it work in this case too
        print(f"ERROR : the picture {picture} has no exif data ! I will ignore it.")
        img.close()
        process_failed_pictures(picture)