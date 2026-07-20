import streamlit as st
from from_trace import *
import pandas as pd
import pydeck as pdk
from pydeck.data_utils import compute_view
from streamlit_folium import st_folium
import folium

class Display():
    def __init__(self):
        load_settings()

        self.pages = {
            "home": st.Page(self.home_page, title="Home"),  
            "manual": st.Page(self.manual_editing, title="Manual editing"),
            "map": st.Page(self.location_display, title="Location display"),
            "picture_upload": st.Page(self.picture_management, title="Picture management"),
            "gpx_upload": st.Page(self.gpx_management, title="gpx management"),
            "import_from_gpx": st.Page(self.edit_from_gpx, title="Import location from GPX"),
            "settings": st.Page(self.settings, title="Settings")
        }

        p = list(self.pages.values())
        pg = st.navigation(p, position="sidebar", expanded=False)
        pg.run()


    def home_page(self):
        st.title("Welcome on photo locator !")

        st.text("Let's start editing your photos' location. Choose what you want to do.")

        with st.container(horizontal=True, horizontal_alignment="distribute"):
            if st.button(label="Manual editing", icon=":material/edit:"):
                st.switch_page(self.pages["manual"])

            if st.button(label="Location display", icon=":material/map:"):
                st.switch_page(self.pages["map"])

            if st.button(label="Picture management", icon=":material/upload:"):
                st.switch_page(self.pages["picture_upload"])

            if st.button(label="GPX files management", icon=":material/conversion_path:"):
                st.switch_page(self.pages["gpx_upload"])

            if st.button(label="Import from GPX", icon=":material/wand_stars:"):
                st.switch_page(self.pages["import_from_gpx"])

            if st.button(label="Settings", icon=":material/settings:"):
                st.switch_page(self.pages["settings"])

    def picture_management(self):
        st.title("Picture management")

        self.display_pictures_files("Updated / not yet processed pictures")
        self.display_failed_pictures()

        st.header("Upload new pictures")

        new_pictures = st.file_uploader(label="Add new pictures", type="image", max_upload_size=1000, accept_multiple_files=True)

        # We have to save the new pictures
        for pict in new_pictures:
            path = get_pict_path(pict.name)
            with open(path, "wb") as f:
                f.write(pict.getvalue())
        
        if len(new_pictures) > 0:
            st.switch_page(self.pages["picture_upload"])


        st.header("Remove pictures")

        to_delete = st.multiselect(
            label="Choose the pictures you want to delete",
            key=1,
            options=get_all_pictures(),
            persist_state="page"
        )

        with st.container(horizontal_alignment="center"):
            if st.button(label="Delete the selected pictures", icon="⚠️", help="Warning : you won't be able to recover these pictures !"):
                for pict  in to_delete:
                    delete_picture(pict)

                st.write("Done !")

        st.header("Download your pictures")

        with st.container(horizontal=True, horizontal_alignment="distribute"):
            st.download_button(
                label="Download successfully processed pictures", 
                help="If pictures have not been processed yet, this will dowload all of them.",
                data = get_zip_successful_data,
                file_name="successfull_pictures.zip",
                icon=":material/download:"
            )

            st.download_button(
                label="Download the failed pictures", 
                help="If pictures have not been processed yet, this will be empty.",
                data = get_zip_failed_data,
                file_name="failed_pictures.zip",
                icon=":material/download:"
            )
    
    def gpx_management(self):
        st.title("Manage GPX files")

        st.header("Current gpx files :")
        self.display_gpx_files()

        st.header("Upload new files")

        new_gpx = st.file_uploader(label="Add new pictures", type=".gpx", max_upload_size=20, accept_multiple_files=True)

        # We have to save the new pictures
        for g in new_gpx:
            path = get_gpx_path(g.name)
            with open(path, "wb") as f:
                f.write(g.getvalue())
        
        if len(new_gpx) > 0:
            st.switch_page(self.pages["gpx_upload"])


        st.header("Remove gpx files")

        to_delete = st.multiselect(
            label="Choose the files you want to delete",
            key=2,
            options=get_all_gpxs_files(),
            persist_state="page"
        )

        with st.container(horizontal_alignment="center"):
            if st.button(label="Delete the selected files", icon="⚠️", help="Warning : you won't be able to recover these files !"):
                for g  in to_delete:
                    delete_gpx(g)

                st.write("Done !")

    def location_display(self):
        st.title("Location of your pictures")
        
        data = get_picts_details()
        loc_data = {
            "files": data["files"],
            "Latitude": data["Latitude"],
            "Longitude": data["Longitude"]
        }
        p = pd.DataFrame(loc_data)
        # line by gemini, see if relevant TODO
        p = pd.DataFrame(loc_data).dropna(subset=["Latitude", "Longitude"])

        pictures_layer = pdk.Layer(
            "ScatterplotLayer",
            data=p,
            
            pickable=True,
            opacity=0.8,
            stroked=True,
            filled=True,
            radius_scale=6,
            radius_min_pixels=5,
            radius_max_pixels=100,
            line_width_min_pixels=1,
            get_position=["Longitude", "Latitude"],
            get_radius=0.5,
            get_fill_color=[255, 0, 0, 140],
            get_line_color=[0, 0, 0],
        )


        if len(p["Longitude"]) == 1:
            print(p)
            # aims at centering the view
            view = pdk.ViewState(
                longitude=p["Longitude"][0], 
                latitude=p["Latitude"][0],
                zoom=15, 
                bearing=0, 
                pitch=0
            )
        elif len(p["Longitude"]) == 0:
            view = view = pdk.ViewState(
                longitude=2.8, 
                latitude=48,
                zoom=3, 
                bearing=0, 
                pitch=0
            )

            st.error("Warning : none of the current pictures have a location")
        else :
            view = compute_view(
                points = [[long, lat] for long, lat in zip(loc_data["Longitude"], loc_data["Latitude"]) if lat != None and long != None]
            )
            view.zoom -= 1

        
        # TODO : make the Longitude and latitude display have only 2 or thre decimal digits
        deck = pdk.Deck(
            [pictures_layer],
            initial_view_state=view,
            tooltip={"text": "{files}\n({Longitude}, {Latitude})"},
            map_style=pdk.map_styles.CARTO_LIGHT
        )

        st.pydeck_chart(deck)

        with st.expander(label="Pictures gallery", expanded=False):
            picts = get_picts_details()
            paths = [get_pict_path(p) for p in picts["files"]]
            captions = [f"{picts["files"][i]} at {picts["Time"][i]}, lat : {picts["Latitude"][i]}, long : {picts["Longitude"][i]}" for i in range(len(picts["files"]))]

            st.image(paths, caption=captions)

    
    def manual_editing(self):
        st.title("Manual editing")

        to_edit = st.multiselect(
            label="Choose the pictures you want to edit",
            key=3,
            options=get_all_pictures(),
            persist_state="page"
        )

        DEFAULT_LATITUDE = 48.85
        DEFAULT_LONGITUDE = 2.37

        st.header("Choose the position manually ...")

        with st.container(horizontal=True, horizontal_alignment="distribute"):
            form_lat = st.number_input(
                label = "Latitude",
                min_value=-90.0,
                max_value=90.0,
                value=DEFAULT_LATITUDE,
                step=0.01,
                key=4,
                persist_state="page"
            )

            form_long = st.number_input(
                label = "Longitude",
                min_value=-90.0,
                max_value=90.0,
                value=DEFAULT_LONGITUDE,
                step=0.01,
                key=5,
                persist_state="page"
            )

        st.map(
            data={
                "Latitude": [form_lat],
                "Longitude": [form_long]
            },
            latitude="Latitude",
            longitude="Longitude"
        )

        if st.button(label="Apply the position chosen manually", help="Warning : this can't be undone", icon=":material/edit:"):
            self.add_position(to_edit, {"latitude": form_lat, "longitude":form_long})

        st.header("Or select the position on the map !")


        m = folium.Map(location=[DEFAULT_LATITUDE, DEFAULT_LONGITUDE], zoom_start=10)

        # The code below will be responsible for displaying 
        # the popup with the latitude and longitude shown
        m.add_child(folium.LatLngPopup())

        f_map = st_folium(m, width=725)

        map_lat = DEFAULT_LATITUDE
        map_long = DEFAULT_LONGITUDE

        if f_map.get("last_clicked"):
            selected_latitude = f_map["last_clicked"]["lat"]
            selected_longitude = f_map["last_clicked"]["lng"]

        with st.container(horizontal=True, horizontal_alignment="center"):
            form = st.form("Position entry form", border=False, width="content")

            submit = form.form_submit_button(label="Choose this position")

        if submit:
            if selected_latitude == DEFAULT_LATITUDE and selected_longitude == DEFAULT_LONGITUDE:
                st.warning("Selected position has default values!")
            st.success(f"Stored position: {selected_latitude:.4f}, {selected_longitude:.4f}")


        if st.button(label="Apply the position chosen on the map", help="Warning : this can't be undone", icon=":material/map:"):
            self.add_position(to_edit, {"latitude": map_lat, "longitude":map_long})

    def edit_from_gpx(self):
        st.title("Add location using gpx files")

        st.header("Current gpx files :")
        ok = self.display_gpx_files()

        with st.container(horizontal_alignment="center"):
            if st.button(label="Change uploaded gpx files"):
                st.switch_page(self.pages["gpx_upload"])

        st.header("Current pictures :")
        ok = self.display_pictures_files("Pictures which will be processed") and ok

        with st.container(horizontal_alignment="center"):
            if st.button(label="Change uploaded pictures"):
                st.switch_page(self.pages["picture_upload"])

        st.text("If the files are good, you can now launch the import of location. The pictures with no " \
        "time won't be processed.")
        st.text("Be aware that the location currently contained in the pictures will be erased (if there is one).")

        with st.container(horizontal_alignment="center"):
            if st.button(label="Begin import", disabled=(not ok)):
                import_from_trace()
                st.text("Import finished !")

                # Display pictures wich were edited or not
                st.header("Results")
                self.display_pictures_files("Successfully processed pictures")
                self.display_failed_pictures()

                with st.container(horizontal_alignment="center"):
                    if st.button(label="See the locations !"):
                        st.switch_page(self.pages["map"])


    def settings(self):
        """
        This page aims at allowing the user to select the paths used, and some other constants
        so he can modify pictures directly in his folders without uploading.
        """

        st.title("Settings")
        st.header("Paths")

        st.text_input(
            label="The path containing the two following paths",
            value=st.session_state.PATH,
            placeholder="You can enter a path or let it empty.",
            on_change=store_settings,
            key="PATH"
        )

        st.text_input(
            label="The path containing the pictures to be edited, subdir of PATH",
            value=st.session_state.PHOTOS_PATH,
            placeholder="You can enter a path or let it empty.",
            on_change=store_settings,
            key="PHOTOS_PATH"
        )

        st.text_input(
            label="The path containing the pictures which failed to be editer, subdir of PATH",
            value=st.session_state.FAILED_PATH,
            placeholder="You can enter a path or let it empty.",
            on_change=store_settings,
            key="FAILED_PATH"
        )

        st.text_input(
            label="The path containing the pictures which were edited successfully",
            value=st.session_state.SUCCESS_PATH,
            placeholder="You can enter a path or let it empty.",
            on_change=store_settings,
            key="SUCCESS_PATH"
        )


        st.header("Camera's advance / late")

        st.text("This aims at allowing you to set the advance / late of your camera compared to the real time." \
        "It will allow the app to work better if this is precise.")


        with st.container(horizontal=True, horizontal_alignment="distribute"):
            st.number_input(
                "Days",
                value=st.session_state.TIME_ADVANCE_days,
                step=1,
                on_change=store_settings,
                key="TIME_ADVANCE_days"
            )

            st.number_input(
                label="Hours",
                min_value=-23,
                max_value=23,
                value=st.session_state.TIME_ADVANCE_hours,
                on_change=store_settings,
                key="TIME_ADVANCE_hours"
            )

            st.number_input(
                label="Minutes",
                min_value=-59,
                max_value=59,
                value=st.session_state.TIME_ADVANCE_minutes,
                on_change=store_settings,
                key="TIME_ADVANCE_minutes"
            )

            st.number_input(
                label="Seconds",
                min_value=-59,
                max_value=59,
                value=st.session_state.TIME_ADVANCE_seconds,
                on_change=store_settings,
                key="TIME_ADVANCE_seconds"
            )
        

        st.header("Delta time point")

        st.write("This parameter is only used when using gpx files. Here, you set the maximum time to a point in the " \
        "gpx file that can considered. That is to say that, if you set it to 10 seconds and that any point in the " \
        "gpx file is at less than ten seconds of the moment at which you took the picture, no position will be " \
        "given to this picture.")

        with st.container(horizontal=True, horizontal_alignment="distribute"):
            st.number_input(
                "Days",
                value=st.session_state.EPSILON_days,
                step=1,
                key="EPSILON_days",
                on_change=store_settings
            )

            st.number_input(
                label="Hours",
                min_value=-23,
                max_value=23,
                value=st.session_state.EPSILON_hours,
                key="EPSILON_hours",
                on_change=store_settings
            )

            st.number_input(
                label="Minutes",
                min_value=-59,
                max_value=59,
                value=st.session_state.EPSILON_minutes,
                key="EPSILON_minutes",
                on_change=store_settings
            )

            st.number_input(
                label="Seconds",
                min_value=-59,
                max_value=59,
                value=st.session_state.EPSILON_seconds,
                key="EPSILON_seconds",
                on_change=store_settings
            )


        st.header("Camera timezone")

        st.write("The timezone of your camera. Only useful when importing from gpx.")

        try:
            index = pytz.all_timezones.index(st.session_state.CAMERA_TIMEZONE)
        except ValueError :
            index = None

        st.selectbox(
            key="CAMERA_TIMEZONE",
            label="Camera timezone",
            options=pytz.all_timezones,
            placeholder="No timezone selected",
            on_change=store_settings,
            index=index
        )


    def add_position(self, picts, pos):
        failed = []
        for pict in picts:
            res = picture_add_position(pict, pos=pos)

            if not res:
                failed.append(pict)

        st.success(f"Done, with {len(failed)} uneditted pictures.")

        if len(failed) > 0:
            with st.expander(label="Failled pictures :", expanded=False):
                for pict in failed:
                    st.error(f"{pict} failed !")
        
    def display_gpx_files(self) -> bool:
        """
        Displays the gpx files in an expandable container

        Returns False if there is no files, True otherwise
        """
        files = get_all_gpxs_files()

        if files == None or len(files) == 0:
            st.error("There is no files or the path doesn't exist !")
            return False

        with st.expander(label = f"GPX files to use ({len(files)})", expanded = False):
            data = {
                "GPX files": files
            }

            st.dataframe(data)

        return True

    def display_pictures_files(self, message: str) -> bool:
        """
        Displays the list of the picture files

        Params:
            message (str): The message displayed on the axpandable menu

        Returns:
            True if pictures found, False otherwise
        """
        pict_data = get_picts_details()

        if pict_data == None or len(pict_data) == 0:
            st.error("There are no pictures or the path doesn't exist !")
            return False

        with st.expander(label = f"{message} ({len(pict_data["files"])})", expanded=False):
            
            st.dataframe(pict_data)

        return True

    def display_failed_pictures(self):
        pict_data = get_failed_pictures()

        if pict_data == None or len(pict_data) == 0:
            st.write("No failed pictures")
            return

        with st.expander(label = f"Pictures which failed to be updated ({len(pict_data["Pictures"])})", expanded=False):
            
            st.dataframe(pict_data)




if __name__ == "__main__":
    d = Display()
