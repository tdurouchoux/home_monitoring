import logging
import logging.config
import os
import time
from pathlib import Path
from typing import Dict

import click
from dotenv import load_dotenv
from reactivex.scheduler import ThreadPoolScheduler

from home_monitoring import config
from home_monitoring.sensors import SENSORS

load_dotenv()


@click.command()
@click.argument("config_directory")
def main(config_directory: str) -> None:
    logger_config, monitoring_config = config.load_config(Path(config_directory))
    mqtt_config = monitoring_config.mqtt
    sensors_config = monitoring_config.sensors

    logging.config.dictConfig(logger_config)
    logger = logging.getLogger("main")

    logger.info("Starting monitoring:")
    logger.info(
        "MQTT configuration: %s",
        {
            "broker": mqtt_config.broker,
            "port": mqtt_config.port,
            "base_topic": mqtt_config.base_topic,
        },
    )

    logger.info("Setting up measurements ... ")

    scheduler = ThreadPoolScheduler(len(sensors_config))

    for sensor in sensors_config:
        logger.info("Setting up sensor %s ...", sensor.name)

        sensor_publisher = SENSORS[sensor.type](sensor, mqtt_config)
        sensor_publisher.create_observable(scheduler)
        sensor_publisher.start_monitoring()

    while True:
        time.sleep(10_000)


if __name__ == "__main__":
    main()
