import psutil

from home_monitoring.sensor_publisher import IntervalSensorPublisher


class SystemUsagePublisher(IntervalSensorPublisher):
    def get_measure(self) -> dict:
        system_measures = {}

        if self.sensor_config.parameters.get("cpu", False):
            system_measures["cpu_usage"] = psutil.cpu_percent()
        if self.sensor_config.parameters.get("ram", False):
            system_measures["ram_usage"] = psutil.virtual_memory().percent
        if self.sensor_config.parameters.get("memory", False):
            system_measures["memory_usage"] = psutil.disk_usage("/").percent
        if self.sensor_config.parameters.get("temperature", False):
            system_measures["cpu_temperature"] = psutil.sensors_temperatures()[
                "cpu_thermal"
            ][0].current

        return system_measures
