from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from omegaconf import MISSING, OmegaConf

LOGGING_CONFIG_FILE = "logging_config.yaml"


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
class SensorConfig:
    type: str = MISSING
    name: str = MISSING
    location: str = MISSING
    nb_retry_measure: int = 3
    qos: int = 1
    retain: bool = False
    period: Optional[int] = None
    buffer_time: Optional[int] = None
    buffer_op: Optional[str] = None
    parameters: Optional[dict[str, str | int | bool]] = None


@dataclass
class MonitoringConfig:
    mqtt: MQTTConfig = field(default_factory=MQTTConfig)
    sensors: list[SensorConfig] = field(default_factory=lambda: [SensorConfig()])


def load_config(config_file: Path) -> tuple[dict, MonitoringConfig]:
    # Load logging config
    with open(LOGGING_CONFIG_FILE, "r") as file:
        logging_config = yaml.safe_load(file.read())

    default_config = OmegaConf.structured(MonitoringConfig)
    file_config = OmegaConf.load(config_file)
    merged_config = OmegaConf.merge(default_config, file_config)

    monitoring_config = OmegaConf.to_object(merged_config)

    return logging_config, monitoring_config
