import datetime as dt
import json
import streamlit as st


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

        "PICTURE_FORMATS": st.session_state.PICTURE_FORMATS,
        "NB_PICTS_BY_LINE": st.session_state.NB_PICTS_BY_LINE
    }

    with open("settings.json", "w") as f:
        json.dump(dic, f, indent=4)

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

def convert_lat_long(pos):
    """
    to convert the pos extraceted from exif
    """
    if pos == None or pos[0] == None:
        return None, None

    lat = pos[0][0][0] / pos[0][0][1] + pos[0][1][0] / (60 * pos[0][1][1]) + pos[0][2][0] / (3600 * pos[0][2][1])
    long = pos[1][0][0] / pos[1][0][1] + pos[1][1][0] / (60 * pos[1][1][1]) + pos[1][2][0] / (3600 * pos[1][2][1])

    return (lat, long)
