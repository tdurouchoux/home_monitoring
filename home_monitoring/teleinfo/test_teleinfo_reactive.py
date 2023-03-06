import serial
import reactivex as rx

# Set up serial port
ser = serial.Serial(
    port="/dev/ttyS0",
    baudrate=1200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.SEVENBITS,
    timeout=1,
)


def read_serial(observer):
    while True:
        data = ser.readline().decode().rstrip()
        observer.on_next(data)


print("opened serial connection")

observable = rx.create(lambda observer, _: read_serial(observer))


print("Finished building observable")
observable.subscribe(print)
