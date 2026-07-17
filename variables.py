import datetime as dt

PATH = ""
PHOTOS_PATH = "pictures"
GPXS_PATH = "gpxs"
FAILED_PATH = "failed"
# the number of seconds of margin for th closest position
# so, if a position exists at less than EPSILON seconds of its taken time, it will be 
# considered valid, otherwise not. If None, there is no limit
EPSILON = dt.timedelta(minutes=50)
# the minutes of advance the camera has on the real time
TIME_ADVANCE = dt.timedelta(minutes=6, seconds=13)

CAMERA_TIMEZONE = "Europe/Paris"

PICTURE_FORMATS = [".JPG", ".jpg"]