# Photo locator

To launch the app, you will need to have streamlit being installed. You can install it using `pip install streamlit`. Then, you can use the following command : `streamlit run frontend.py` and the app is now launched !

## Functionning

Everything can be done using the graphic interface. The script will not alter the content of youo picture, that is to say that the script only modifies the exif data of your picture, and nothing else !
It only works with pictures in jpeg.

## Settings

The settings allow you to chose the directory to process. So, if you want to process pictures in a directory on your computer, you can make the `path` be this directory, the pictures path to nothing, and then you will be able to process your pictures. 
The camera timezone is only useful when using a gpx file.

## Importing location from gpx

This script will use all the gpx files provided, look for the closest point from the time at which your picture was taken, and make this position be the one of your picture. Hence, your pictures need to have a time. Be carefull wether your camera is on time or not, and if it is note the cases, you can change it in the `Settings` tab of the app.


The app currently works, the only thing to know is that the success_path has not yet been implemented.