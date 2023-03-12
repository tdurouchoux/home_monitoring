from typing import Dict
import logging

from datetime import timedelta
import reactivex as rx

from home_monitoring.utils import logger_factory, handle_errors_observable
from home_monitoring.influxdb.influxdb_connector import InfluxDBConnector
from home_monitoring.openweather.openweather_api import CurrentWeatherApi

CURR_WEATHER_MEASUREMENT_NAME = "openweather_current_weather"


def monitor_openweather(
    influxdb_config: Dict,
    period: int,
    current_weather_location: str,
    nb_retry: int = 3,
    log_file: str = None,
    log_level=logging.INFO,
):
    if log_file is not None:
        logger = logger_factory("openweather", log_file, log_level=log_level)
    else:
        logger = logging

    logger.info("Setting up current weather openweather api ...")

    current_weather_api = CurrentWeatherApi(current_weather_location, logger=logger)

    logger.info("Setting up influxdb connection ...")

    influxdb_connector = InfluxDBConnector(
        influxdb_config["database"],
        influxdb_config["username"],
        influxdb_config["password"],
        logger=logger,
    )

    logger.info(
        f"Creating openweather api observable making requests every {period} seconds"
    )

    openweather_obs = rx.interval(period=timedelta(seconds=period)).pipe(
        rx.operators.map(lambda i: current_weather_api.query_api())
    )
    openweather_obs = handle_errors_observable(openweather_obs, nb_retry, logger=logger)

    influxdb_connector.write_observable(CURR_WEATHER_MEASUREMENT_NAME, openweather_obs)

    logger.info(f"Launching {CURR_WEATHER_MEASUREMENT_NAME} measures ...")
