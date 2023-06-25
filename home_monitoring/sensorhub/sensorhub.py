from typing import Dict
import logging
from datetime import timedelta

import reactivex as rx
from reactivex.scheduler import ThreadPoolScheduler

from home_monitoring.utils import logger_factory, handle_errors_observable
from home_monitoring.sensorhub.sensor_connector import SensorConnector
from home_monitoring.influxdb.influxdb_connector import InfluxDBConnector

MEASUREMENT_NAME = "sensorhub"


def monitor_sensors(
    influxdb_config: Dict,
    scheduler: ThreadPoolScheduler,
    period: int,
    nb_retry: int = 2,
    log_file: str = None,
    log_level=logging.INFO,
) -> None:
    if log_file is not None:
        logger = logger_factory("sensorhub", log_file, log_level=log_level)
    else:
        logger = logging

    logger.info("Setting up sensorhub connection ...")

    sensor_connector = SensorConnector(logger=logger)

    logger.info("Setting up influxdb connection ...")

    influxdb_connector = InfluxDBConnector(
        influxdb_config["database"],
        influxdb_config["username"],
        influxdb_config["password"],
        logger=logger,
    )

    logger.info(
        f"Creating sensorhub observable taking measurement every {period} seconds"
    )

    sensor_obs = rx.interval(period=timedelta(seconds=period)).pipe(
        rx.operators.map(lambda i: sensor_connector.get_all_sensors()),
        rx.operators.subscribe_on(scheduler),
    )
    sensor_obs = handle_errors_observable(sensor_obs, nb_retry, logger=logger)

    influxdb_connector.write_observable(MEASUREMENT_NAME, sensor_obs)

    logger.info(f"Launching {MEASUREMENT_NAME} measures ...")
