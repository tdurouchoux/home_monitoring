import logging
import logging.config
import time
from pathlib import Path

import typer
import yaml
from dotenv import load_dotenv
from reactivex.scheduler import ThreadPoolScheduler

from home_monitoring import config
from home_monitoring.sensors import SENSORS

load_dotenv()

app = typer.Typer()


def init_command(
    config_file: str,
    debug: bool = False,
) -> tuple[logging.Logger, config.MQTTConfig, list[config.SensorConfig]]:
    logger_config, monitoring_config = config.load_config(Path(config_file))

    # Update logging config if debug mode is enabled
    if debug:
        logger_config["root"]["level"] = "DEBUG"
        logger_config["handlers"]["console_handler"]["level"] = "DEBUG"

    logging.config.dictConfig(logger_config)
    logger = logging.getLogger("main")

    return logger, monitoring_config.mqtt, monitoring_config.sensors


@app.command()
def monitor(
    config_file: str,
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
) -> None:
    logger, mqtt_config, sensors_config = init_command(config_file, debug)

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


@app.command()
def ha_config(
    config_file: str,
    output_file: str = typer.Option(
        "homeassistant_mqtt.yaml",
        "--output",
        "-o",
        help="Output YAML file for Home Assistant configuration",
    ),
) -> None:
    """
    Generate Home Assistant MQTT sensor configuration from monitoring config.
    """
    logger, mqtt_config, sensors_config = init_command(config_file)

    sensors_ha_config = []

    for sensor in sensors_config:
        logger.info("Setting up sensor %s ...", sensor.name)

        sensor_publisher = SENSORS[sensor.type](sensor, mqtt_config)
        sensors_ha_config += sensor_publisher.get_ha_configuration()

    with open(output_file, "w") as f:
        yaml.dump(sensors_ha_config, f)

    logger.info("Home Assistant configuration generated successfully.")


if __name__ == "__main__":
    app()
