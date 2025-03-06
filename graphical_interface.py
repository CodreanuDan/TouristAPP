#***********************************************************************
# MODULE: graphical_interface
# SCOPE:  GUI interface for current project
# REV: 1.0
#
# Created by: Codreanu Dan

#***********************************************************************
# IMPORTS:
from datetime import datetime as dt
import streamlit as st
import requests
from streamlit_javascript import st_javascript
import pandas as pd
import json
import os


# ***********************************************************************
# CONTENT: Streamlit_GUI_HandleOpenMeteoData
# INFO: Aux class for project GUI, handles data from OpenMeteo API https://open-meteo.com/ 
class Streamlit_GUI_HandleOpenMeteoData():
    """
        :Class name: Streamlit_GUI_HandleOpenMeteoData
        :Descr:  Aux class for project GUI, handles data from OpenMeteo API https://open-meteo.com/ 
    """
    def __init__(self):
        self.w_json_file =  os.path.join(os.path.dirname(__file__), "data/weather_data.json")
        self.__html_file_path = os.path.join(os.path.dirname(__file__), "html/forecast.html")
        self.__style_css_path = os.path.join(os.path.dirname(__file__), "styles/weekly_forecast_style.css")
    
    def __load_weather_data(self, json_file):
        """ 
            Load weather data from JSON file 
                :param: filename -> weather data JSON file
                :type: str
        """
        try:
            with open(json_file, "r") as file:
                data = [json.loads(line) for line in file]
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"[❌][graphical_interface.py/Streamlit_GUI_HandleOpenMeteoData/load_weather_data] --> Error while loading data: {e}")
            print(f"[❌][graphical_interface.py/Streamlit_GUI_HandleOpenMeteoData/load_weather_data] --> Error while loading data: {e}")
            return None

    def display_weather_data(self):
        """ 
            Display weather data in Streamlit interface
            :param: df -> dataframe
        """
        df = self.__load_weather_data(self.w_json_file)
        if df is None or df.empty:
            st.warning("[❌] No weather data available!")
            return

        # Check relevant columns
        required_columns = ['date', 'temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'uv_index', 'precipitation_probability']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.warning(f"[❌] Some required columns are missing from the data! Missing columns: {missing_columns}")
            return

        # Convert timestamp to standard unit, second from millisecond
        df["date"] = pd.to_datetime(df["date"] // 1000, unit='s')

        # Extract day from data
        df["day"] = df["date"].dt.date

        # Aggregate data for 1 day
        daily_summary = df.groupby("day").agg({
            "temperature_2m": "mean",
            "relative_humidity_2m": "mean",
            "wind_speed_10m": "mean",
            "uv_index": "mean",
            "precipitation_probability": "max"
        }).reset_index()

        # Verificăm dacă avem date pentru 168h/1 săptămână
        if len(daily_summary) > 7:
            daily_summary = daily_summary.tail(7)

        # Dictionary of weather conditions with corresponding emoji
        weather_icons = {
            0: "☀️",  # Clear
            1: "🌤️",  # Partly cloudy
            2: "☁️",  # Cloudy
            3: "🌧️",  # Rainy
            4: "❄️",  # Snow
            5: "🌬️",  # Windy
            6: "🌫️",  # Fog
            7: "🌩️",  # Thunderstorm
            8: "🌈",   # Rainbow
            9: "🌪️",  # Tornado
        }

        # Days of the week mapping
        day_of_week_map = {
            0: "Luni",
            1: "Marți",
            2: "Miercuri",
            3: "Joi",
            4: "Vineri",
            5: "Sâmbătă",
            6: "Duminică"
        }
        
        #**********************************************************************************************
        # Open style.css file
        with open(self.__style_css_path, "r") as f:
            css = f.read()
        # Apply custom CSS style
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

        #**********************************************************************************************
        # HTML 
        # Create container to wrap columns and make them expand horizontally
        st.markdown('<div class="weather-container">', unsafe_allow_html=True)
        # Create weekly forecast columns (horizontal alignment)
        cols = st.columns(len(daily_summary))  # Create as many columns as the number of days
        for i, col in enumerate(cols):
            with col:
                row = daily_summary.iloc[i]
                day_of_week = row['day'].weekday()
                # Get the corresponding day name 
                day_name = day_of_week_map.get(day_of_week, "N/A")
                precipitation_probability = row.get('precipitation_probability', 0)  
                if precipitation_probability > 50:
                    weather_icon = weather_icons[3]  # Rainy (🌧️)
                elif row['temperature_2m'] < 2 and precipitation_probability > 50:
                    weather_icon = weather_icons[4]  # Snow (❄️)
                elif row['precipitation_probability'] > 80:
                    weather_icon = weather_icons[7]  # Thunderstorm (🌩️)
                elif row['wind_speed_10m'] > 20:
                    weather_icon = weather_icons[5]  # Windy (🌬️)
                elif row['relative_humidity_2m'] > 80 and row['temperature_2m'] < 15:
                    weather_icon = weather_icons[6]  # Fog (🌫️)
                else:
                    weather_icon = weather_icons[1]  # Partly Cloudy (🌤️)
                
                #**********************************************************************************************
                # Open html file
                with open(self.__html_file_path, "r", encoding="utf-8") as f:
                    forecast_html = f.read()
                # Replace placeholders in the HTML with actual data
                forecast_html = forecast_html.replace("{day_name}", day_name)
                forecast_html = forecast_html.replace("{weather_icon}", weather_icon)
                forecast_html = forecast_html.replace("{date}", str(row['day']))
                forecast_html = forecast_html.replace("{temperature}", str(f"{row['temperature_2m']:.2f}°C"))
                forecast_html = forecast_html.replace("{humidity}", str(f"{row['relative_humidity_2m']:.2f}%"))
                forecast_html = forecast_html.replace("{wind_speed}", str(f"{row['wind_speed_10m']:.2f} km/h"))
                forecast_html = forecast_html.replace("{uv_index}", str(f"{row['uv_index']:.2f}"))
                # Display the weather information in a horizontal column
                st.markdown(f'<div class="weather-column">{forecast_html}</div>',unsafe_allow_html=True)
        # End container div
        st.markdown('</div>', unsafe_allow_html=True)
                
#***********************************************************************
# CONTENT: Streamlit_GUI_HandleOpenStreetMap
# INFO:Aux class for project GUI, handles data from OpenStreetMap API "https://nominatim.openstreetmap.org/search"
class Streamlit_GUI_HandleOpenStreetMap():
    """
        :Class name: Streamlit_GUI_HandleOpenStreetMap
        :Descr:  Aux class for project GUI, handles location data from JSON file
    """
    def __init__(self):
        self.l_json_file = os.path.join(os.path.dirname(__file__), "data\location_data.json")
        self.__html_file_path = os.path.join(os.path.dirname(__file__), "html/location.html")
        self.__style_css_path = os.path.join(os.path.dirname(__file__), "styles/location_style.css")

    def __load_location_data(self, location_file):
        """ 
            Load location data from JSON file
                :param: location data json
        """
        try:
            with open(location_file, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data
        except Exception as e:
            st.error(f"[❌][graphical_interface.py/Streamlit_GUI_HandleOpenStreetMap/load_location_data] --> Error while loading location data: {e}")
            print(f"[❌][graphical_interface.py/Streamlit_GUI_HandleOpenStreetMap/load_location_data] --> Error while loading location data: {e}")
            return None

    def display_location_data(self):
        """  Display location data in Streamlit interface """
        #**********************************************************************************************
        location_data = self.__load_location_data(self.l_json_file)
        if not location_data:
            st.warning("[❌][graphical_interface.py/Streamlit_GUI_HandleOpenStreetMap/display_location_section] --> No location data available!")
            print("[❌][graphical_interface.py/Streamlit_GUI_HandleOpenStreetMap/display_location_section] --> No location data available!")
            return
        #**********************************************************************************************
        # Box Ttile and descr
        location_title = "Location Information"
        location_info = "This section displays the location data based on OpenStreetMap."
        # Extract values from the loaded location data (replace these with actual JSON keys)
        location_name = location_data.get('name', 'N/A')
        country_code = location_data.get('country_code', 'N/A')
        latitude = location_data.get('latitude', 'N/A')
        longitude = location_data.get('longitude', 'N/A')
        # Extract region from the location name (assumed to be the second part after splitting by comma)
        region = location_name.split(',')[1].strip() if len(location_name.split(',')) > 1 else 'N/A'  # Take the second part
        # Get the image URL for the location from Pexels API
        location_image_url = self.__get_location_image(region)
        
        #**********************************************************************************************
        # Open style.css file
        with open(self.__style_css_path, "r") as f:
            css = f.read()
        # Apply custom CSS style
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        
        #**********************************************************************************************
        # Open html file
        with open(self.__html_file_path, "r", encoding="utf-8") as f:
            location_html = f.read()
        # Replace placeholders in the HTML file with actual data
        location_html = location_html.replace("{location_title}", location_title)
        location_html = location_html.replace("{location_info}", location_info)
        location_html = location_html.replace("{location_name}", location_name)
        location_html = location_html.replace("{country_code}", country_code)
        location_html = location_html.replace("{latitude}", str(latitude))
        location_html = location_html.replace("{longitude}", str(longitude))
        # If the image URL exists, replace the placeholder with the actual image URL
        if location_image_url:
            location_html = location_html.replace("{location_image}", location_image_url)
        else:
            # Set a default image if none found
            location_html = location_html.replace("{location_image}", "img/default_placeholder.jpg")  
        # Inject HTML into Streamlit
        st.markdown(f"""{location_html}""", unsafe_allow_html=True)
        
    def __get_location_image(self,location_name: str) -> str:
        """
            Get image URL for the respective location from Pexels API
                :param: location_name
                :return: image_url|str
        """
        url = "https://api.pexels.com/v1/search"
        PEXELS_API_KEY = "lgxGutSPWdcVMBPbsos0JFMvYyFCQQhpSeWkMzAgYevTGuFs6pZz5QwN"
        headers = {"Authorization": PEXELS_API_KEY}
        params = {"query": location_name, "per_page": 1}

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            if data.get("photos"):
                return data["photos"][0]["src"]["original"]
        return None  
    
    
#***********************************************************************
# CONTENT: Streamlit_GUI
# INFO: Class for project GUI, made with Streamlit
class Streamlit_GUI(Streamlit_GUI_HandleOpenMeteoData, Streamlit_GUI_HandleOpenStreetMap):
    """ 
        :Class name: Streamlit_GUI
        :Descr: Class for project GUI, made with Streamlit
        :Inherits from: Streamlit_GUI_HandleOpenMeteoData,
                        Streamlit_GUI_HandleOpenStreetMap
    """
    def __init__(self):
        super().__init__()
        Streamlit_GUI_HandleOpenStreetMap.__init__(self)
        Streamlit_GUI_HandleOpenMeteoData.__init__(self)
        self.run_gui()

    def run_gui(self):
        st.title('Toursim Info')
        self.display_location_data()
        self.display_weather_data()


#***********************************************************************
# DBG_AREA:
if __name__ == "__main__":
    pass
