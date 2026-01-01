import psutil

from home_monitoring.sensor_publisher import IntervalSensorPublisher


class SystemUsagePublisher(IntervalSensorPublisher):
    MODEL = "RPI"
    MESSAGE_CONTENT: dict[str, dict] = {
        "cpu_usage": {
            "name": "CPU Usage",
            "state_class": "measurement",
            "unit_of_measurement": "%",
            "value_template": "{{ value_json.cpu_usage }}",
        },
        "ram_usage": {
            "name": "RAM Usage",
            "state_class": "measurement",
            "unit_of_measurement": "%",
            "value_template": "{{ value_json.ram_usage }}",
        },
        "memory_usage": {
            "name": "Memory Usage",
            "state_class": "measurement",
            "unit_of_measurement": "%",
            "value_template": "{{ value_json.memory_usage }}",
        },
        "cpu_temperature": {
            "name": "CPU Temperature",
            "device_class": "temperature",
            "state_class": "measurement",
            "unit_of_measurement": "°C",
            "value_template": "{{ value_json.cpu_temperature }}",
        },
    }

    def get_measure(self) -> dict:
        return {
            "cpu_usage": psutil.cpu_percent(),
            "ram_usage": psutil.virtual_memory().percent,
            "memory_usage": psutil.disk_usage("/").percent,
            "cpu_temperature": psutil.sensors_temperatures()["cpu_thermal"][0].current,
        }
