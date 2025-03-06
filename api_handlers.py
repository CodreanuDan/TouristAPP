#***********************************************************************
# MODULE: api_handlers
# SCOPE:  Request data from APIs
# REV: 1.0
#
# Created by: Codreanu Dan

#***********************************************************************
# IMPORTS:
import openmeteo_requests
import requests_cache
import pandas as pd
import os
from retry_requests import retry
import requests
import json


#***********************************************************************
# CONTENT: OpenMeteoHdl
# INFO:    Request data from meteo service: https://open-meteo.com/
class OpenMeteoHdl():
    """
        :Class name: OpenMeteoHdl
        :Descr: Request data from meteo service: https://open-meteo.com/
    """
    def __init__(self, forecast_hours:int):
        """
        Initialize the OpenMeteoHdl instance with necessary parameters.
            :param latitude: Latitude of the location for weather data.
            :param longitude: Longitude of the location for weather data.
            :param forecast_hours: Number of hours to forecast, default is 24.
        """
        # Setup the Open-Meteo API client with cache and retry on error
        self.cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
        self.retry_session = retry(self.cache_session, retries = 5, backoff_factor = 0.2)
        self.openmeteo = openmeteo_requests.Client(session = self.retry_session)
        self.__filename="data/weather_data.json"
        self.dbg_file_weather =  self.__filename
        self.__location_data="data/location_data.json"
        
        self.latitude = float(self.__get_location_data(location_data= self.__location_data)[0])
        self.longitude = float(self.__get_location_data(location_data= self.__location_data)[1])
        self.forecast_hours = forecast_hours
        
        # Weather parameters
        self.url = "https://api.open-meteo.com/v1/forecast"
        self.params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "hourly": ["temperature_2m", "relative_humidity_2m", "dew_point_2m",
                       "apparent_temperature", "precipitation_probability", "precipitation",
                       "rain", "showers", "snowfall", "snow_depth",
                       "visibility", "wind_speed_10m", "uv_index",
                       "uv_index_clear_sky", "is_day"],
            "timezone": "auto",
            # Number of hours to forecast
            "forecast_hours": self.forecast_hours  
        }
    
    def fetch_weather_data(self):
        """
            Fetch the weather data from the Open-Meteo API.
                :return: DataFrame with hourly weather data
        """
        try:
            responses = self.openmeteo.weather_api(self.url, params=self.params)
            if not responses:
                print("[❌][api_handlers.py/OpenMeteoHdl/fetch_weather_data] --> No weather data returned!")
                return None
            
            # Process first response (you can loop through multiple if needed)
            response = responses[0]
            
            # print(f"[🌥️][api_handlers.py/OpenMeteoHdl/fetch_weather_data] --> Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
            # print(f"[🌥️][api_handlers.py/OpenMeteoHdl/fetch_weather_data] --> Elevation: {response.Elevation()} m asl")
            # print(f"[🌥️][api_handlers.py/OpenMeteoHdl/fetch_weather_data] --> Timezone: {response.Timezone()} {response.TimezoneAbbreviation()}")
            # print(f"[🌥️][api_handlers.py/OpenMeteoHdl/fetch_weather_data] --> Timezone difference to GMT+0: {response.UtcOffsetSeconds()} s")
            
            # Process hourly data
            hourly = response.Hourly()
            hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
            hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
            hourly_dew_point_2m = hourly.Variables(2).ValuesAsNumpy()
            hourly_apparent_temperature = hourly.Variables(3).ValuesAsNumpy()
            hourly_precipitation_probability = hourly.Variables(4).ValuesAsNumpy()
            hourly_precipitation = hourly.Variables(5).ValuesAsNumpy()
            hourly_rain = hourly.Variables(6).ValuesAsNumpy()
            hourly_showers = hourly.Variables(7).ValuesAsNumpy()
            hourly_snowfall = hourly.Variables(8).ValuesAsNumpy()
            hourly_snow_depth = hourly.Variables(9).ValuesAsNumpy()
            hourly_visibility = hourly.Variables(10).ValuesAsNumpy()
            hourly_wind_speed_10m = hourly.Variables(11).ValuesAsNumpy()
            hourly_uv_index = hourly.Variables(12).ValuesAsNumpy()
            hourly_uv_index_clear_sky = hourly.Variables(13).ValuesAsNumpy()
            hourly_is_day = hourly.Variables(14).ValuesAsNumpy()

            # Prepare data into a DataFrame
            hourly_data = {
                "date": pd.date_range(
                    start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                    end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                    freq=pd.Timedelta(seconds=hourly.Interval()),
                    inclusive="left"
                ),
                "temperature_2m": hourly_temperature_2m,
                "relative_humidity_2m": hourly_relative_humidity_2m,
                "dew_point_2m": hourly_dew_point_2m,
                "apparent_temperature": hourly_apparent_temperature,
                "precipitation_probability": hourly_precipitation_probability,
                "precipitation": hourly_precipitation,
                "rain": hourly_rain,
                "showers": hourly_showers,
                "snowfall": hourly_snowfall,
                "snow_depth": hourly_snow_depth,
                "visibility": hourly_visibility,
                "wind_speed_10m": hourly_wind_speed_10m,
                "uv_index": hourly_uv_index,
                "uv_index_clear_sky": hourly_uv_index_clear_sky,
                "is_day": hourly_is_day
            }

            # Create a pandas DataFrame from the hourly data
            hourly_dataframe = pd.DataFrame(data=hourly_data)
            
            # Save to JSON
            weather_data = self.__filename
            self.__save_to_json(dataframe=hourly_dataframe, filename= weather_data)
            
            return hourly_dataframe
        
        except Exception as e:
            print(f"[❌][api_handlers.py/OpenMeteoHdl/fetch_weather_data] --> Error while fetching weather data: {e}")
            return None
    
    def __save_to_json(self, dataframe: pd.DataFrame, filename: str):
        """
            Save the DataFrame to a JSON file.
                :param dataframe: The pandas DataFrame containing weather data.
                :param filename: The name of the file to save the data to.
        """
        try:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"[🗑️][api_handlers.py/OpenMeteoHdl/save_to_json] --> File {filename} deleted before loading new data.")
            dataframe.to_json(filename, orient='records', lines=True)
            print(f"[✅][api_handlers.py/OpenMeteoHdl/save_to_json] --> Wather data saved in: {filename}")
        except Exception as e:
            print(f"[❌][api_handlers.py/OpenMeteoHdl/save_to_json] --> Saving data in JSON file not possible! Error: {e}")

    def __get_location_data(self,location_data: str)-> list:
        """
            Load location coord, latitude and longitude from JSON file
                :param location_data: The JSON containing location data.
                :return: list -> [0]:latitude  [1]:longitude
        """
        coord = []
        try:
            if os.path.exists(location_data):
                with open(location_data, 'r', encoding= 'utf-8') as file:
                    data = json.load(file)
                    coord.append(data['latitude'])
                    coord.append(data['longitude'])
                    print(print(f"[✅][api_handlers.py/OpenStreetMapHdl/__get_location_data] -->  lat:{coord[0]} lon: {coord[1]}"))
                    return coord
            else:
                print(print(f"[❌][api_handlers.py/OpenStreetMapHdl/__get_location_data] -->  {location_data} doesn`t exist: {e}"))
        except Exception as e:
            print(f"[❌][api_handlers.py/OpenStreetMapHdl/__get_location_data] -->  Error getting location data: {e}")
        return [0.0, 0.0]
                
                  
#***********************************************************************
# CONTENT: OpenStreetMapHdl
# INFO:    Request data from location api service: "https://nominatim.openstreetmap.org/search"
class OpenStreetMapHdl():
    """
        :Class name: OpenStreetMapHdl
        :Descr: Request data from location api service: "https://nominatim.openstreetmap.org/search"
    """
    def __init__(self, location_name: str):
        """
            Initialize the handler for querying OpenStreetMap.
                :param location_name: Name of the location to be queried.
        """
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.__filename = "data/location_data.json"
        self.dbg_file_location = self.__filename
        self.location_name = location_name
        
    def get_location(self):
        """
        Fetches location data based on the name using the OpenStreetMap API.
        
        :return: dict containing location data or error message.
        """
        params = {
            "q": self.location_name,
            "format": "json",
            "limit": 1,  # Limit to the first result
            "addressdetails": 1,  # Include address details
            "extratags": 1,  # Include extra tags
        }

        headers = {
            "User-Agent": "YourAppName/1.0 (contact@yourdomain.com)"  # Replace with your app's name and contact email
        }

        response = requests.get(self.base_url, params=params, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data:
                result = data[0]

                location_data = {
                    "name": result.get("display_name", "Unknown"),
                    "latitude": result.get("lat", "N/A"),
                    "longitude": result.get("lon", "N/A"),
                    "type": result.get("type", "N/A"),
                    "country_code": result.get("address", {}).get("country_code", "N/A"),
                    "postcode": result.get("address", {}).get("postcode", "N/A"),
                    "bounding_box": result.get("boundingbox", []),
                    "osm_id": result.get("osm_id", "N/A"),
                    "population": result.get("extratags", {}).get("population", "N/A")
                }

                # Save the data to a JSON file
                locationData_file = self.__filename
                self.__save_to_json(location_data, filename= locationData_file)

                return location_data
            else:
                print(f"[❌][api_handlers.py/OpenStreetMapHdl/get_location] -->  Location not found!")
                return {"[❌][api_handlers.py/OpenStreetMapHdl/get_location]": "Location not found!"}
        else:
            print(f"[❌][api_handlers.py/OpenStreetMapHdl/get_location] --> Request failed with status code {response.status_code}")
            return {"[❌][api_handlers.py/OpenStreetMapHdl/get_location]": f"Request failed with status code {response.status_code}"}

    def __save_to_json(self, location_data:dict, filename):
        """
        Save the fetched location data to a JSON file.
        
        :param location_data: The location data to save.
        """
        try:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"[🗑️][api_handlers.py/OpenStreetMapHdl/__save_to_json] --> File {filename} deleted before loading new data.")

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(location_data, f, indent=4)

            print(f"[✅][api_handlers.py/OpenStreetMapHdl/__save_to_json] --> Location data saved in: {filename}")
        except Exception as e:
            print(f"[❌][api_handlers.py/OpenStreetMapHdl/__save_to_json] -->  Error saving location data: {e}")
     
            
#***********************************************************************
# DBG_AREA:
if __name__ == "__main__":
    # latitude = 52.52
    # longitude = 13.41
    forecast_hours = 168  # You can set this to the desired number of hours
    
    # Instantiate the OpenMeteoHdl class and fetch weather data
    location_handler = OpenStreetMapHdl("Baia Mare")
    meteo_handler = OpenMeteoHdl(forecast_hours)
    location_data = location_handler.get_location()
    weather_data = meteo_handler.fetch_weather_data()
    if weather_data is not None:
        print(f"[🪲][DEBUG][<api_handlers.py>] Response from open-meteo.com is saved in json file: {meteo_handler.dbg_file_weather}")
    if location_data is not None:
        print(f"[🪲][DEBUG][<api_handlers.py>] Response from OpenStreetMap is saved in json file: {location_handler.dbg_file_location}")