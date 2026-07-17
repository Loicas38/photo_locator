import streamlit as st
from from_trace import *
from variables import *
from frontend_utils import *
import pandas as pd
import pydeck as pdk
from pydeck.data_utils import compute_view

class Display():
    def __init__(self):
        self.pages = {
            "home": st.Page(self.home_page, title="Home"),  
            "manual": st.Page(self.manual_editing, title="Manual editing"),
            "map": st.Page(self.location_display, title="Location display"),
            "picture_upload": st.Page(self.upload_pictures, title="Pictures upload"),
            "gpx_upload": st.Page(self.upload_gpxs, title="Upload gpx files"),
            "import_from_gpx": st.Page(self.edit_from_gpx, title="Import location from GPX")
        }

        p = list(self.pages.values())
        pg = st.navigation(p, position="sidebar", expanded=False)
        pg.run()

    def manual_editing(self):
        st.title("Manual editing")

    def location_display(self):
        st.title("Location of your pictures")
        
        data = get_picts_details()
        p = pd.DataFrame(data)
        # line by gemini, see if relevant TODO
        p = pd.DataFrame(data).dropna(subset=["Latitude", "Longitude"])

        pictures_layer = pdk.Layer(
            "ScatterplotLayer",
            data=p,
            
            pickable=True,
            opacity=0.8,
            stroked=True,
            filled=True,
            radius_scale=6,
            radius_min_pixels=10,
            radius_max_pixels=100,
            line_width_min_pixels=1,
            get_position=["Longitude", "Latitude"],
            get_radius=0.5,
            get_fill_color=[255, 0, 0, 140],
            get_line_color=[0, 0, 0],
        )


        if len(p["Longitude"] > 1):
            # aims at centering the view
            view = pdk.ViewState(
                longitude=p["Longitude"][0], 
                latitude=p["Latitude"][0],
                zoom=15, 
                bearing=0, 
                pitch=0
            )
        else :
            view = compute_view(
                points = [[long, lat] for long, lat in zip(data["Longitude"], data["Latitude"]) if lat != None and long != None]
            )

        

        deck = pdk.Deck(
            [pictures_layer],
            initial_view_state=view,
            tooltip={"text": "{files}"},
        )

        st.pydeck_chart(deck)

    def upload_pictures(self):
        st.title("pictures upload")

        st.header("Current pictures :")
        self.display_pictures_files("Current pictures")

    def upload_gpxs(self):
        st.title("Upload gpx files")

        st.header("Current gpx files :")
        self.display_gpx_files()

    def edit_from_gpx(self):
        st.title("Add location using gpx files")

        st.header("Current gpx files :")
        self.display_gpx_files()

        with st.container(horizontal_alignment="center"):
            if st.button(label="Change uploaded gpx files"):
                st.switch_page(self.pages["gpx_upload"])

        st.header("Current pictures :")
        self.display_pictures_files("Pictures which will be processed")

        with st.container(horizontal_alignment="center"):
            if st.button(label="Change uploaded pictures"):
                st.switch_page(self.pages["picture_upload"])

        st.text("If the files are good, you can now launch the import of location.")
        st.text("Be aware that the location contained in the pictures will be erased.")

        with st.container(horizontal_alignment="center"):
            if st.button(label="Begin import"):
                import_from_trace()
                st.text("Import finished !")

                # Display pictures wich were edited or not
                st.header("Results")
                self.display_pictures_files("Successfully processed pictures")
                self.display_failed_pictures()

                with st.container(horizontal_alignment="center"):
                    if st.button(label="See the locations !"):
                        st.switch_page(self.pages["map"])

        
    def display_gpx_files(self):
        """
        Displays the gpx files in an expandable container
        """
        files = get_all_gpxs_files()

        with st.expander(label = f"GPX files to use ({len(files)})", expanded = False):
            data = {
                "GPX files": files
            }

            st.dataframe(data)

    def display_pictures_files(self, message: str):
        """
        Displays the list of the picture files

        Params:
            message (str): The message displayed on the axpandable menu
        """
        pict_data = get_picts_details()

        with st.expander(label = f"{message} ({len(pict_data["files"])})", expanded=False):
            
            st.dataframe(pict_data)

    def display_failed_pictures(self):
        pict_data = get_failed_pictures()

        with st.expander(label = f"Pictures which failed to be updated ({len(pict_data["Pictures"])})", expanded=False):
            
            st.dataframe(pict_data)

    def home_page(self):
        st.title("Welcome on photo locator !")

        st.text("Let's start editing youor photos' location. Choose what you want to do.")

        with st.container(horizontal=True, horizontal_alignment="distribute"):
            if st.button(label="Manual editing"):
                st.switch_page(self.pages["manual"])

            if st.button(label="Location display"):
                st.switch_page(self.pages["map"])

            if st.button(label="Pictures upload"):
                st.switch_page(self.pages["picture_upload"])

            if st.button(label="GPX files upload"):
                st.switch_page(self.pages["gpx_upload"])

            if st.button(label="Import from GPX"):
                st.switch_page(self.pages["import_from_gpx"])



if __name__ == "__main__":
    d = Display()
