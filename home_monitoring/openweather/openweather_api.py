from abc import ABC, abstractmethod
import logging
import requests
from datetime import datetime

API_KEY = "892584c6da65b957cfa46b34d183cc83"


class OpenweatherApi(ABC):
    def __init__(self, logger=logging) -> None:
        self.logger = logger

    @staticmethod
    def extract_data_json(response_dict, mapping):
        data_extract = dict()

        for field, response_fields in mapping.items():
            if isinstance(response_fields, tuple):
                aux = response_dict.copy()
                for rfield in response_fields:
                    if (
                        isinstance(rfield, str)
                        and isinstance(aux, dict)
                        and rfield in aux
                    ) or (
                        isinstance(rfield, int)
                        and isinstance(aux, list)
                        and rfield < len(aux)
                    ):
                        aux = aux[rfield]
                    else:
                        aux = None
                        break
                if not aux is None:
                    data_extract[field] = aux
            else:
                if response_fields in response_dict:
                    data_extract[field] = response_dict[response_fields]

        return data_extract

    def query_api(self) -> dict:
        self.logger.debug("Sending request to api.")
        response = requests.get(self.query)
        self.logger.debug("Response received.")

        response_dict = response.json()

        weather_info = self.extract_data_json(response_dict, self.mapping)

        return weather_info


class CurrentWeatherApi(OpenweatherApi):
    raw_query = (
        "http://api.openweathermap.org/data/2.5/weather?q={}&appid={}&units=metric"
    )

    mapping = {
        "weather_category": ("weather", 0, "main"),
        "weather_description": ("weather", 0, "description"),
        "temp": ("main", "temp"),
        "temp_feels_like": ("main", "feels_like"),
        "pressure": ("main", "pressure"),
        "humidity": ("main", "humidity"),
        "wind_speed": ("wind", "speed"),
        "wind_direction": ("wind", "deg"),
        "wind_gust": ("wind", "gust"),
        "cloud_cover": ("clouds", "all"),
    }

    def __init__(self, city: str, logger=logging) -> None:
        super().__init__(logger=logger)

        self.query = self.raw_query.format(city, API_KEY)
