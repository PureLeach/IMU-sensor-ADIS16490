import time  # Library for working with time
import spidev  # Library for working with the SPI interface


# Initializing the SPI interface
spi = spidev.SpiDev()  # Creating an SPI object
spi.open(0, 0)  # Selecting the port number and device number (CS) of the SPI bus
spi.max_speed_hz = 15000000  # Setting the maximum speed of the SPI bus
spi.mode = 3  # SPI mode selection (0 to 3)


def spi_read(spi, reg):  # SPI data reading function
    send = [0]*2  # Creating a list of two elements
    # In the 0 cell of the list, write the address that is specified in the reg parameter
    send[0] = reg
    spi.writebytes(send)  # Sending bytes over the SPI bus
    # Read 2 bytes over the SPI bus. As a result, we get a list of two values [X, Y]
    resp = spi.readbytes(2)
    # Shift 8 bits of cell 0 to the left, then use the log.addition with cell 1
    ret = ((resp[0] << 8) | resp[1])
    return ret


def spi_write(spi, reg, data):  # SPI data recording function
    send = [0]*2  # Creating a list of two elements
    # In the 0 cell of the list, write the address that we specify in 
    # the reg parameter and use OR to specify the highest bit for writing
    send[0] = 0x80 | reg
    send[1] = data  # In 1 cell we send the data that needs to be recorded
    spi.writebytes(send)  # Sending bytes over the SPI bus


def check(val, bits):  # Function for checking the value for a sign
    if((val & (1 << (bits-1))) != 0):  
        val = val - (1 << bits)
    return val


def temp_out(temp):  # Thermometer data processing function
    temp = check(temp, 16)  # Sending data to the sign verification function
    # Applying the temperature calculation formula from the datasheet
    return 0.01429 * temp + 25


def gyro_out(gyro):  # Gyroscope data processing function
    gyro = check(gyro, 16)  # Sending data to the sign verification function
    return gyro * 0.005  # Multiply by the coefficient from the datasheet


def acc_out(acc):  # The function of processing the accelerometer data
    acc = check(acc, 16)  # Sending data to the sign verification function
    return acc * 0.5  # Multiply by the coefficient from the datasheet


# Main loop
try:
    while True:
        spi_write(spi, 0x00, 0x00)  # Select the 0 pages
        print('SYS_E_FLAG (0x0 = нет ошибок)', hex(spi_read(spi, 0x08)))
        print('DIAG_STS (0x0 = нет ошибок)', hex(spi_read(spi, 0x0A)))
        print('ID', spi_read(spi, 0x7E))

        # Reading sensor data
        xgyro = spi_read(spi, 0x12)
        xgyro = gyro_out(xgyro)
        ygyro = spi_read(spi, 0x16)
        ygyro = gyro_out(ygyro)
        zgyro = spi_read(spi, 0x1A)
        zgyro = gyro_out(zgyro)
        xacc = spi_read(spi, 0x1E)
        xacc = acc_out(xacc)
        yacc = spi_read(spi, 0x22)
        yacc = acc_out(yacc)
        zacc = spi_read(spi, 0x26)
        zacc = acc_out(zacc)
        temp = spi_read(spi, 0x0E)
        temp = temp_out(temp)

        spi_write(spi, 0x00, 0x03)  # Select the 3 pages
        spi_write(spi, 0x0D, 0x10)  # Сhange DEC_RATE
        spi_write(spi, 0x0C, 0x99)  # Сhange DEC_RATE

        # Output data to the console
        print("Температура:   ", "{:10.4f}".format(temp), " degС")
        print("X гироскоп:   ", "{:10.4f}".format(xgyro), " deg/s")
        print("Y гироскоп:   ", "{:10.4f}".format(ygyro), " deg/s")
        print("Z гироскоп:   ", "{:10.4f}".format(zgyro), " deg/s")
        print("X акселерометр:   ", "{:10.4f}".format(xacc), " mg")
        print("Y акселерометр:   ", "{:10.4f}".format(yacc), " mg")
        print("Z акселерометр:   ", "{:10.4f}".format(zacc), " mg")
        print('NULL_CNFG (должен быть = 0x70A на 3 стр) ',
              hex(spi_read(spi, 0x0E)))
        print('Decrate', spi_read(spi, 0x0C))
        time.sleep(1)  # Delay between data updates


except KeyboardInterrupt:  # Press Ctrl+C
    spi.close()  # Disabling the SPI bus connection
