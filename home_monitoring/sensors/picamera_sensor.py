import base64
import io
import logging
from datetime import datetime

from picamera2 import Picamera2

from home_monitoring import config
from home_monitoring.sensor_publisher import IntervalSensorPublisher

logger = logging.getLogger(__name__)


class PiCameraPublisher(IntervalSensorPublisher):
    MODEL: str = "Raspberry Pi Camera 3"
    MESSAGE_CONTENT: dict[str, dict] = {
        "image": {
            "name": "Camera Image",
            "value_template": "{{ value_json.timestamp }}",
            "json_attributes_topic": "~/attributes",
            "json_attributes_template": "{{ value_json | tojson }}",
        },
    }

    def __init__(
        self,
        sensor_config: config.SensorConfig,
        mqtt_config: config.MQTTConfig,
    ) -> None:
        super().__init__(
            sensor_config,
            mqtt_config,
        )

        # Initialize camera
        self.camera = Picamera2()

        # Get parameters with defaults
        params = sensor_config.parameters or {}
        self.resolution = params.get("resolution", (1920, 1080))
        self.format = params.get("format", "JPEG")
        self.quality = params.get("quality", 85)

        # Configure camera
        camera_config = self.camera.create_still_configuration(
            main={"size": self.resolution}
        )
        self.camera.configure(camera_config)
        self.camera.start()

        logger.info(
            "Pi Camera initialized with resolution %s, format %s, quality %s",
            self.resolution,
            self.format,
            self.quality,
        )

    def get_measure(self) -> dict:
        # Capture image to memory
        stream = io.BytesIO()
        self.camera.capture_file(stream, format=self.format.lower())
        stream.seek(0)

        # Encode as base64
        image_data = base64.b64encode(stream.read()).decode("utf-8")

        return {
            "timestamp": datetime.now().isoformat(),
            "image": image_data,
            "format": self.format,
            "resolution": f"{self.resolution[0]}x{self.resolution[1]}",
        }

    def __del__(self):
        # Clean up camera on deletion
        if hasattr(self, "camera"):
            self.camera.stop()
            self.camera.close()
