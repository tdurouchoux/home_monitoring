import serial
import time
from tqdm import tqdm

def read_trame(ser):

    trame = []

    line = ser.readline()
    trame.append(line.decode("utf-8"))

    while b'\x03' not in line:
        line = ser.readline()
        trame.append(line.decode("utf-8"))

    return trame

with serial.Serial(port='/dev/ttyS0',
                   baudrate=1200,
                   parity=serial.PARITY_NONE,
                   stopbits=serial.STOPBITS_ONE,
                   bytesize=serial.SEVENBITS,
                   timeout=1) as ser:    
    line = ser.readline()
    
    # Wait for starting character
    while b'\x02' not in line:
        line = ser.readline()

    list_time_taken = []

    for i in tqdm(range(100)):
        starting_time = time.perf_counter()
        trame = read_trame(ser)
        if len(trame) != 10:
            print('Read trame failed somehow...')
        else:
            list_time_taken.append(time.perf_counter() - starting_time)

print(f'Mean time taken :{sum(list_time_taken) / len(list_time_taken):.2f}')
print(min(list_time_taken))
print(max(list_time_taken))
