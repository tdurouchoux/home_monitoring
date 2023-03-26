from typing import Dict
import logging
from datetime import timedelta

import psutil
import reactivex as rx
from reactivex.scheduler import ThreadPoolScheduler

from home_monitoring.utils import logger_factory, handle_errors_observable
from home_monitoring.influxdb.influxdb_connector import InfluxDBConnector


def get_system_measures(measure_cpu: bool,
    measure_ram: bool,
    measure_memory: bool,
    measure_temperature: bool) -> Dict:
    system_measures = dict()

    if measure_cpu:
        system_measures["cpu_usage"] = psutil.cpu_percent()
    if measure_ram:
        system_measures["ram_usage"] = psutil.virtual_memory().percent
    if measure_memory:
        system_measures["memory_usage"] = psutil.disk_usage('/').percent
    if measure_temperature:
        system_measures["cpu_temperature"] = psutil.sensors_temperatures()["cpu_thermal"][0].current

    return system_measures


# TODO Use measurement_name parameter for other monitoring scripts
# TODO ABC monitor_info 

def monitor_system(
    influxdb_config: Dict,
    scheduler: ThreadPoolScheduler,
    period: int,
    measurement_name: str = "system",
    measure_cpu: bool = True,
    measure_ram: bool = True,
    measure_memory: bool = True,
    measure_temperature: bool = True,
    nb_retry: int = 2,
    log_file: str = None,
    log_level=logging.INFO,
) -> None:
    if log_file is not None:
        logger = logger_factory(measurement_name, log_file, log_level=log_level)
    else:
        logger = logging

    logger.info("Setting up influxdb connection ...")

    influxdb_connector = InfluxDBConnector(
        influxdb_config["database"],
        influxdb_config["username"],
        influxdb_config["password"],
        logger=logger,
    )

    logger.info(
        f"Creating system observable taking measurement every {period} seconds with :"
    )
    logger.info(f" -> cpu usage : {'enabled' if measure_cpu else 'disabled'}")
    logger.info(f" -> ram usage : {'enabled' if measure_ram else 'disabled'}")
    logger.info(f" -> memory usage : {'enabled' if measure_memory else 'disabled'}")
    logger.info(f" -> cpu temperature : {'enabled' if measure_temperature else 'disabled'}")

    system_obs = rx.interval(period=timedelta(seconds=period)).pipe(
        rx.operators.map(lambda i: get_system_measures(measure_cpu, measure_ram, measure_memory, measure_temperature)),
        rx.operators.subscribe_on(scheduler),
    )
    system_obs = handle_errors_observable(system_obs, nb_retry, logger=logger)

    influxdb_connector.write_observable(measurement_name, system_obs)

    logger.info(f"Launching {measurement_name} measures ...")
