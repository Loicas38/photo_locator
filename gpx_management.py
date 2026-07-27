import os
import gpx
import streamlit as st
import matplotlib as mpl
import folium
import geopandas as gpd
import pandas as pd


def get_all_gpxs() -> list:
    """
    Returns a list of gpx objects
    """
    gpx_path = ""

    if st.session_state["PATH"] != "" and st.session_state["PATH"] != None:
        gpx_path = st.session_state["PATH"]

    if st.session_state["GPXS_PATH"] != None and st.session_state["GPXS_PATH"] != "":
        if gpx_path == "" :
            gpx_path = st.session_state["GPXS_PATH"]
        else:
            gpx_path += "\\" + st.session_state["GPXS_PATH"]

    if not os.path.exists(gpx_path):
        print("ERROR : the path to the gpx files doesn't exist")
        return None

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

    if st.session_state["PATH"] != "" and st.session_state["PATH"] != None:
        gpx_path = st.session_state["PATH"]

    if st.session_state["GPXS_PATH"] != None and st.session_state["GPXS_PATH"] != "":
        if gpx_path == "" :
            gpx_path = st.session_state["GPXS_PATH"]
        else:
            gpx_path += "\\" + st.session_state["GPXS_PATH"]

    if not os.path.exists(gpx_path):
        print("ERROR : the path to the gpx files doesn't exist")
        return None

    gpxs = []
    for entry in os.listdir(gpx_path):
        full_path = os.path.join(gpx_path, entry)

        if os.path.isfile(full_path):
            _, ext = os.path.splitext(full_path)

            if ext == ".gpx":
                gpxs.append(full_path)

    return gpxs

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


def make_map(file_list) -> str:
    colormap = list(map(mpl.colors.to_hex,
                        mpl.colormaps["Set1"].colors))
    map_ = folium.Map()
    gdfs = []
    for file_name, color in zip(file_list, colormap):
        # Read the GPX file into a GeoDataFrame from the "tracks" layer and add
        # it to the list.
        gdf: gpd.GeoDataFrame = gpd.read_file(file_name, layer="tracks")
        gdfs.append(gdf)
        #  Create a FeatureGroup for the current file to hold its polyline and
        # add that to the map
        lines_layer: folium.FeatureGroup = folium.FeatureGroup(name=file_name)
        folium.PolyLine(locations=gdf.geometry.get_coordinates()[["y", "x"]],
                        color=color).add_to(lines_layer)
        lines_layer.add_to(map_)
    # Fit the extent of the map to the tracks
    xmin, ymin, xmax, ymax = pd.concat(gdfs).total_bounds if gdfs\
        else [-50, -50, 50, 50]
    map_.fit_bounds([[ymin, xmin], [ymax, xmax]])
    return folium.Figure().add_child(map_).render()