from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
from typing import Dict, List, Union, Tuple, Optional

from omegaconf import OmegaConf, MISSING
import yaml

LOGGING_CONFIG_FILE = "logging_config.yaml"
MONITORING_CONFIG_FILE = "monitoring_config.yaml"


@dataclass
class InfluxDBConfig:
    database: str = MISSING
    username: str = MISSING
    password: str = MISSING
    host: str = "localhost"
    port: int = 8086


@dataclass
class WriteConfiguration:
    batch_size: int = 1
    max_retries: int = 2
    retry_interval: int = 400
    flush_interval: int = 1_000_000


@dataclass
class MeasurementConfig:
    implement: str = MISSING
    name: str = MISSING
    write_options: WriteConfiguration = field(default_factory=WriteConfiguration)
    nb_retry_measure: int = 3
    period: Optional[int] = None
    parameters: Optional[Dict[str, Union[str, int]]] = None


@dataclass
class MonitoringConfig:
    influxdb: InfluxDBConfig = field(default_factory=InfluxDBConfig)
    measurements: List[MeasurementConfig] = field(
        default_factory=lambda: [MeasurementConfig()]
    )


def load_config(config_directory: Path) -> Tuple[Dict, MonitoringConfig]:
    # Load logging config
    with open(config_directory / LOGGING_CONFIG_FILE, "r") as file:
        logging_config = yaml.safe_load(file.read())

    default_config = OmegaConf.structured(MonitoringConfig)
    file_config = OmegaConf.load(config_directory / MONITORING_CONFIG_FILE)
    merged_config = OmegaConf.merge(default_config, file_config)

    monitoring_config = OmegaConf.to_object(merged_config)

    return logging_config, monitoring_config
