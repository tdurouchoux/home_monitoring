import logging

import reactivex as rx
import serial
from reactivex import operators as ops

from home_monitoring import config
from home_monitoring.sensor_publisher import SensorPublisher

logger = logging.getLogger(__name__)

# Exemple de frame:
# {
#  'BASE': '123456789'       # Index heure de base en Wh
#  'OPTARIF': 'HC..',        # Option tarifaire HC/BASE
#  'IMAX': '007',            # Intensité max
#  'HCHC': '040177099',      # Index heure creuse en Wh
#  'IINST': '005',           # Intensité instantanée en A
#  'PAPP': '01289',          # Puissance Apparente, en VA
#  'MOTDETAT': '000000',     # Mot d'état du compteur
#  'HHPHC': 'A',             # Horaire Heures Pleines Heures Creuses
#  'ISOUSC': '45',           # Intensité souscrite en A
#  'ADCO': '000000000000',   # Adresse du compteur
#  'HCHP': '035972694',      # index heure pleine en Wh
#  'PTEC': 'HP..'            # Période tarifaire en cours
# }


class FailedChecksumError(Exception):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __str__(self):
        return f"Failed checksum test on key :{self.key} wit value {self.value}"


class TeleinfoConnector:
    # clés téléinfo

    # clés avec une valeur entière
    LOG_KEYS = ["BASE", "IINST", "PAPP"]
    INT_MEASURE_KEYS = ["BASE", "IMAX", "IINST", "PAPP"]

    BAUD_RATE = 1200
    TIMEOUT = 1

    def __init__(self, serial_port) -> None:
        self.serial_port = serial_port

    @staticmethod
    def verif_checksum(data, checksum) -> bool:
        data_unicode = 0
        for caractere in data:
            data_unicode += ord(caractere)

        sum_unicode = (data_unicode & 63) + 32

        return checksum == chr(sum_unicode)

    def _get_serial_context(self) -> serial.Serial:
        return serial.Serial(
            port=self.serial_port,
            baudrate=self.BAUD_RATE,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.SEVENBITS,
            timeout=self.TIMEOUT,
        )

    def _wait_for_frame_start(self, ser: serial.Serial):
        logger.debug("Waiting for frame start ...")

        line = ser.readline()
        while b"\x02" not in line:  # recherche du caractère de début de frame
            line = ser.readline()

    def _read_frame(self, ser: serial.Serial, all_keys: bool = False) -> dict:
        frame = dict()
        line = ""

        while b"\x03" not in line:
            line = ser.readline()
            line_str = line.decode("utf-8")

            [key, val, *_] = line_str.split(" ")

            if not all_keys and key not in self.LOG_KEYS:
                continue

            checksum = (line_str.replace("\x03\x02", ""))[-3:-2]

            logger.debug(
                f"Parsed following information : key=%s val=%s checksum=%s",
                key,
                val,
                checksum,
            )

            if self.verif_checksum(f"{key} {val}", checksum):
                # creation du champ pour la frame en cours avec cast des valeurs de mesure en "integer"
                frame[key] = int(val) if key in self.INT_MEASURE_KEYS else val
            else:
                raise FailedChecksumError(key, val)

        logger.debug(f"Received teleinfo measures: {frame}")

        return frame

    def get_single_frame(self, all_keys: bool = False):
        with self._get_serial_context() as ser:
            self._wait_for_frame_start(self, ser)

            logger.debug("Frame start detected, starting monitoring ...")
            frame = self._read_frame(ser, all_keys=all_keys)
            logger.debug(f"Received teleinfo measures: {frame}")
            return frame

    def log_teleinfo_serial(self, observer):
        logger.debug("Starting serial listening ...")

        with self._get_serial_context() as ser:
            self._wait_for_frame_start(self, ser)

            logger.debug("Frame start detected, starting monitoring ...")
            while True:
                frame = self._read_frame(ser)
                observer.on_next(frame)


class TeleinfoPublisher(SensorPublisher):
    MODEL: str = "TELEINFO"
    MESSAGE_CONTENT: dict[str, dict] = {
        "BASE": {
            "name": "Total energy",
            "device_class": "energy",
            "state_class": "total",
            "unit_of_measurement": "Wh",
            "value_template": "{{ value_json.BASE }}",
        },
        "IINST": {
            "name": "Current",
            "device_class": "current",
            "state_class": "measurement",
            "unit_of_measurement": "A",
            "value_template": "{{ value_json.IINST }}",
        },
        "PAPP": {
            "name": "Apparent power",
            "device_class": "apparent_power",
            "state_class": "measurement",
            "unit_of_measurement": "VA",
            "value_template": "{{ value_json.PAPP }}",
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

        self.teleinfo_connector = TeleinfoConnector(
            self.sensor_config.parameters["serial_port"]
        )

    def create_observable(self, scheduler) -> None:
        self.measure_obs = rx.create(
            lambda observer, _: self.teleinfo_connector.log_teleinfo_serial(observer)
        ).pipe(ops.observe_on(scheduler), ops.subscribe_on(scheduler))
