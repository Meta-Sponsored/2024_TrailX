import serial
import time

# arduino = serial.Serial('/dev/ttyACM0', 115200, timeout=5)

arduino = serial.Serial(
    port="/dev/ttyUSB0",
    baudrate=115200,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=5,
    xonxoff=False,
    rtscts=False,
    dsrdtr=False,
    write_timeout=2,
)

while True:
    try:
        arduino.write("hello_from_jetson".encode())
        # data = arduino.readline()
        # if data:
        #     print(data)
        time.sleep(1)
    except Exception as e:
        print(e)
        arduino.close()
