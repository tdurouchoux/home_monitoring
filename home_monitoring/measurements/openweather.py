from abc import ABC, abstractmethod
from datetime import datetime
import logging
import requests
from typing import Dict

from home_monitoring.measurement_logger import IntervalMeasurementLogger
from home_monitoring import config


class OpenweatherApi(ABC):
    def __init__(self, api_key: str, logger=logging) -> None:
        self.api_key = api_key
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

    def __init__(self, city: str, api_key: str, logger=logging) -> None:
        super().__init__(api_key, logger=logger)

        self.query = self.raw_query.format(city, self.api_key)


class OpenWeatherLogger(IntervalMeasurementLogger):
    def __init__(
        self,
        measurement_config: config.MeasurementConfig,
        influxdb_config: config.InfluxDBConfig,
    ) -> None:
        super().__init__(
            measurement_config,
            influxdb_config,
        )

        self.current_weather_api = CurrentWeatherApi(
            self.measurement_config.parameters["city"],
            self.measurement_config.parameters["api_key"],
        )

    def get_measure(self) -> Dict:
        return self.current_weather_api.query_api()
