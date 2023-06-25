from smbus import SMBus
from bme280 import BME280


bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)


print(f"Temperature : {bme280.get_temperature()}")
print(f"Humidity : {bme280.get_humidity()}")
print(f"Pressure : {bme280.get_pressure()}")
