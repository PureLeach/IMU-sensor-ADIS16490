import time
from typing import Union

import spidev


# Initializing the SPI interface
spi: object = spidev.SpiDev()  # Creating an SPI object
spi.open(0, 0)  # Selecting the port number and device number (CS) of the SPI bus
spi.max_speed_hz = 15000000  # Setting the maximum speed of the SPI bus
spi.mode = 3  # SPI mode selection (0 to 3)


def spi_read(spi: object, reg: int) -> int:
    send = [0] * 2
    # In the 0 cell of the list, write the address that is specified in the reg parameter
    send[0] = reg
    # Sending bytes over the SPI bus
    spi.writebytes(send)
    # Read 2 bytes over the SPI bus. As a result, we get a list of two values [X, Y]
    resp = spi.readbytes(2)
    # Shift 8 bits of cell 0 to the left, then use the log.addition with cell 1
    ret = (resp[0] << 8) | resp[1]
    return ret


def spi_write(spi, reg: int, data: Union[float, int]) -> None:
    send = [0] * 2
    # In the 0 cell of the list, write the address that we specify in
    # the reg parameter and use OR to specify the highest bit for writing
    send[0] = 0x80 | reg
    # In 1 cell we send the data that needs to be recorded
    send[1] = data
    # Sending bytes over the SPI bus
    spi.writebytes(send)


# Function for checking the value for a sign
def check(val: Union[int, float], bits: int) -> Union[int, float]:
    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)
    return val


# Thermometer data processing function
def temp_out(temp: float) -> float:
    # Sending data to the sign verification function
    temp = check(temp, 16)
    # Applying the temperature calculation formula from the datasheet
    return 0.01429 * temp + 25


# Gyroscope data processing function
def gyro_out(gyro: int) -> float:
    # Sending data to the sign verification function
    gyro = check(gyro, 16)
    # Multiply by the coefficient from the datasheet
    return gyro * 0.005


# The function of processing the accelerometer data
def acc_out(acc: int) -> float:
    # Sending data to the sign verification function
    acc = check(acc, 16)
    # Multiply by the coefficient from the datasheet
    return acc * 0.5


# Main loop
try:
    while True:
        # Select the 0 pages
        spi_write(spi, 0x00, 0x00)
        print("SYS_E_FLAG (0x0 = without error)", hex(spi_read(spi, 0x08)))
        print("DIAG_STS (0x0 = without error)", hex(spi_read(spi, 0x0A)))
        print("ID", spi_read(spi, 0x7E))

        # Reading sensor data
        xgyro: int = spi_read(spi, 0x12)
        xgyro: float = gyro_out(xgyro)
        ygyro: int = spi_read(spi, 0x16)
        ygyro: float = gyro_out(ygyro)
        zgyro: int = spi_read(spi, 0x1A)
        zgyro: float = gyro_out(zgyro)
        xacc: int = spi_read(spi, 0x1E)
        xacc: float = acc_out(xacc)
        yacc: int = spi_read(spi, 0x22)
        yacc: float = acc_out(yacc)
        zacc: int = spi_read(spi, 0x26)
        zacc: float = acc_out(zacc)
        temp: int = spi_read(spi, 0x0E)
        temp: float = temp_out(temp)

        # Select the 3 pages
        spi_write(spi, 0x00, 0x03)
        # Сhange DEC_RATE
        spi_write(spi, 0x0D, 0x10)
        spi_write(spi, 0x0C, 0x99)

        # Output data to the console
        print("Temperature:   ", "{:10.4f}".format(temp), " degС")
        print("X gyroscope axis:   ", "{:10.4f}".format(xgyro), " deg/s")
        print("Y gyroscope axis:   ", "{:10.4f}".format(ygyro), " deg/s")
        print("Z gyroscope axis:   ", "{:10.4f}".format(zgyro), " deg/s")
        print("X accelerometer axis:   ", "{:10.4f}".format(xacc), " mg")
        print("Y accelerometer axis:   ", "{:10.4f}".format(yacc), " mg")
        print("Z accelerometer axis:   ", "{:10.4f}".format(zacc), " mg")
        print("NULL_CNFG (must be = 0x70A) ", hex(spi_read(spi, 0x0E)))
        print("Decrate", spi_read(spi, 0x0C))
        # Delay between data updates
        time.sleep(1)


except KeyboardInterrupt:
    # Disabling the SPI bus connection
    spi.close()
