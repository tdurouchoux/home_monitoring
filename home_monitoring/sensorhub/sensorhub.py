from typing import Dict
import logging

from home_monitoring.sensorhub.sensor_connector import SensorConnector
from home_monitoring.influxdb.influxdb_connector import InfluxDBConnector

MEASUREMENT_NAME = "sensorhub"


def monitor_sensors(
    influxdb_config: Dict,
    period: int,
    log_file: str = None,
    log_level=logging.INFO,
):
    if log_file is not None:
        logging.basicConfig(
            filename=log_file,
            level=log_level,
            format="%(asctime)s -- %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    sensor_connector = SensorConnector()

    influxdb_connector = InfluxDBConnector(**influxdb_config)

    influxdb_connector.periodic_measures(
        MEASUREMENT_NAME, sensor_connector.get_all_sensors, period
    )
