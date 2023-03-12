from typing import Dict

import os
import click
import yaml
import logging

from home_monitoring.sensorhub import sensorhub
from home_monitoring.openweather import openweather
from home_monitoring.teleinfo import teleinfo
from home_monitoring.utils import logger_factory


def load_config(config_file: str) -> Dict:
    def path_join(loader, node):
        seq = loader.construct_sequence(node)
        return os.path.sep.join(seq)

    def log_level(loader, node):
        level = loader.construct_scalar(node)
        return getattr(logging, level.upper())

    loader = yaml.SafeLoader

    loader.add_constructor("!path_join", path_join)
    loader.add_constructor("!log_level", log_level)

    with open(config_file, "r") as f:
        config = yaml.load(f, Loader=loader)

    return config


@click.command()
@click.argument("config_file")
def main(config_file: str) -> None:
    config = load_config(config_file)

    influxdb_config = config["influxdb"]

    main_logger = logger_factory("launch_monitoring", config["main_log_file"])

    main_logger.info("Starting monitoring, setting up measurements ... ")

    for measurement, m_config in config["measurements"].items():
        main_logger.info(f"Adding measurement {measurement} ...")

        if measurement == "sensorhub":
            sensorhub.monitor_sensors(influxdb_config, **m_config)
        elif measurement == "openweather":
            openweather.monitor_openweather(influxdb_config, **m_config)
        elif measurement == "teleinfo":
            teleinfo.monitor_teleinfo(influxdb_config, **m_config)

    main_logger.info("Finished configuration, launching monitoring ...")

    input()


if __name__ == "__main__":
    main()
