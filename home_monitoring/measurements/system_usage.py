from typing import Dict

import psutil

from home_monitoring.measurement_logger import IntervalMeasurementLogger
from home_monitoring import config


class SystemUsageLogger(IntervalMeasurementLogger):
    def get_measure(self) -> Dict:
        system_measures = {}

        if self.measurement_config.parameters.get("cpu", False):
            system_measures["cpu_usage"] = psutil.cpu_percent()
        if self.measurement_config.parameters.get("ram", False):
            system_measures["ram_usage"] = psutil.virtual_memory().percent
        if self.measurement_config.parameters.get("memory", False):
            system_measures["memory_usage"] = psutil.disk_usage("/").percent
        if self.measurement_config.parameters.get("temperature", False):
            system_measures["cpu_temperature"] = psutil.sensors_temperatures()[
                "cpu_thermal"
            ][0].current

        return system_measures
