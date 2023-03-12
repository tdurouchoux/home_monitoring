import logging

import serial
import reactivex as rx


class FailedChecksumError(Exception):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __str__(self):
        return f"Failed checksum test on key :{key} wit value {value}"


class TeleinfoConnector:
    # Exemple de trame:
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

    # clés téléinfo
    LOG_KEYS = ["BASE", "IMAX", "HHPHC", "IINST", "PAPP"]

    # clés avec une valeur entière
    INT_MEASURE_KEYS = ["BASE", "IMAX", "IINST", "PAPP"]

    BAUD_RATE = 1200
    TIMEOUT = 1

    def __init__(self, serial_port, logger=logging) -> None:
        self.serial_port = serial_port

        self.logger = logger

    @staticmethod
    def verif_checksum(data, checksum) -> bool:
        data_unicode = 0
        for caractere in data:
            data_unicode += ord(caractere)

        sum_unicode = (data_unicode & 63) + 32

        return checksum == chr(sum_unicode)

    def _log_teleinfo_serial(self, observer):
        self.logger.info("Starting serial listening ...")

        with serial.Serial(
            port=self.serial_port,
            baudrate=self.BAUD_RATE,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.SEVENBITS,
            timeout=self.TIMEOUT,
        ) as ser:
            self.logger.info("Waiting for frame start ...")

            line = ser.readline()
            while b"\x02" not in line:  # recherche du caractère de début de trame
                line = ser.readline()

            self.logger.info("Frame start detected, starting monitoring ...")

            trame = dict()
            line = ser.readline()

            while True:
                line_str = line.decode("utf-8")
                self.logger.debug(line)

                [key, val, *_] = line_str.split(" ")

                if key in self.LOG_KEYS:
                    checksum = (line_str.replace("\x03\x02", ""))[-3:-2]

                    self.logger.debug(
                        f"Parsed following information : {key=} {val=} {checksum=}"
                    )

                    if self.verif_checksum(f"{key} {val}", checksum):
                        # creation du champ pour la trame en cours avec cast des valeurs de mesure en "integer"
                        trame[key] = int(val) if key in self.INT_MEASURE_KEYS else val
                    else:
                        raise FailedChecksumError(key, value)

                if b"\x03" in line:
                    self.logger.debug(f"Received teleinfo measures: {trame}")

                    observer.on_next(trame)

                    trame = dict()
                line = ser.readline()

    def create_observable(self):
        return rx.create(lambda observer, _: self._log_teleinfo_serial(observer))
