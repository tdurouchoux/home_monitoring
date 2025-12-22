import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import yaml
from omegaconf import MISSING, OmegaConf

LOGGING_CONFIG_FILE = "logging_config.yaml"
MONITORING_CONFIG_FILE = "monitoring_config.yaml"


@dataclass
class MQTTConfig:
    broker: str = MISSING
    port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None
    base_topic: str = "homeassistant"
    # use_tls: bool = False
    # ca_certs: Optional[str] = None


@dataclass
class MeasurementConfig:
    type: str = MISSING
    name: str = MISSING
    location: str = MISSING
    nb_retry_measure: int = 3
    period: Optional[int] = None
    qos: int = 1
    parameters: Optional[dict[str, str | int | bool]] = None


@dataclass
class MonitoringConfig:
    mqtt: MQTTConfig = field(default_factory=MQTTConfig)
    measurements: list[MeasurementConfig] = field(
        default_factory=lambda: [MeasurementConfig()]
    )


def load_config(config_directory: Path) -> tuple[dict, MonitoringConfig]:
    # Load logging config
    with open(config_directory / LOGGING_CONFIG_FILE, "r") as file:
        logging_config = yaml.safe_load(file.read())

    default_config = OmegaConf.structured(MonitoringConfig)
    file_config = OmegaConf.load(config_directory / MONITORING_CONFIG_FILE)
    merged_config = OmegaConf.merge(default_config, file_config)

    monitoring_config = OmegaConf.to_object(merged_config)

    return logging_config, monitoring_config
