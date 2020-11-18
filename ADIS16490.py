import spidev                   #Библиотека для работы с интерфейсом SPI
import time                     #для работы со временем
import RPi.GPIO as GPIO
#Инициализация интерфейса SPI
spi=spidev.SpiDev()             #Создаём объект SPI
spi.open(0, 0)                  #Выбор номера порта и номера устройства(CS) шины SPI 
spi.max_speed_hz=15000000       #Задаём максимальную скорость работы шины SPI
spi.mode=3                      #Выбор режима работы SPI (от 0 до 3)
GPIO.setmode(GPIO.BOARD)        #Инициализация по номеру пина на гребенке коннектора GPIO
GPIO.setup(29, GPIO.IN)         #Установка режима работы канала на вывод
GPIO.setup(37, GPIO.IN)         #Установка режима работы канала на вывод


def SpiRead(spi,reg):           #Функция считывания данных по SPI
    send=[0]*2                  #Создаём список из двух элементов
    send[0]=reg                 #В 0 ячейку списка записываем адрес, который указываем в параметре reg
    spi.writebytes(send)        #Отправляем байты по шине SPI
    resp=spi.readbytes(2)       #Считываем 2 байта по шине SPI. В итоге получаем список из двух значений [X, Y]
    ret=((resp[0]<<8)|resp[1])  #Сдвигаем 8 бит ячейки 0 влево, затем используем лог.сложение с ячейкой 1
    return ret

def SpiWrite(spi,reg,data):     #Функция записи данных по SPI
    send=[0]*2                  #Создаём список из двух элементов
    send[0]=0x80|reg            #В 0 ячейку списка записываем адрес, который указываем в параметре reg и с помощью лог.ИЛИ указываем старший бит на запись            
    send[1]=data                #В 1 ячейку отправляем данные которые нужно записать
    spi.writebytes(send)        #Отправляем байты по шине SPI
    
def check(val, bits):               #Функция проверки значения на знак 
    if( (val&(1<<(bits-1))) != 0):  #Если отрицательное, то переводим в дополнительный код
        val = val - (1<<bits)       
    return val

def temp_out(temp):             #Функция обработки данных термометра
    temp= check(temp, 16)       #Отправляем данные в функцию проверки знака
    return 0.01429 * temp + 25  #Применяем формулу расчёта температуры из datasheet

def gyro_out(gyro):             #Функция обработки данных гироскопа
    gyro = check(gyro, 16)      #Отправляем данные в функцию проверки знака
    return gyro * 0.005         #Умножаем на коэффициент из datasheet

def acc_out(acc):               #Функция обработки данных акселерометра
    acc= check(acc, 16)         #Отправляем данные в функцию проверки знака
    return acc * 0.5            #Умножаем на коэффициент из datasheet

#Главный цикл
try:
    while True:
        ch_state1 = GPIO.input(29)
        print('ch_state 29', ch_state1)
        ch_state2 = GPIO.input(37)
        print('ch_state 37', ch_state2)
        SpiWrite(spi,0x00,0x00)      #Переключаемся на 0 стр
        print('SYS_E_FLAG (0x0 = нет ошибок)', hex(SpiRead(spi,0x08)))
        print('DIAG_STS (0x0 = нет ошибок)', hex(SpiRead(spi,0x0A)))
        print('ID', SpiRead(spi,0x7E))
                
        #Чтение данных датчика
        xgyro = SpiRead(spi,0x12) 
        xgyro = gyro_out(xgyro) 
        ygyro = SpiRead(spi,0x16) 
        ygyro = gyro_out(ygyro)
        zgyro = SpiRead(spi,0x1A) 
        zgyro = gyro_out(zgyro)
        xacc = SpiRead(spi,0x1E) 
        xacc = acc_out(xacc)
        yacc = SpiRead(spi,0x22) 
        yacc = acc_out(yacc)
        zacc = SpiRead(spi,0x26) 
        zacc = acc_out(zacc)
        temp = SpiRead(spi,0x0E)
        temp = temp_out(temp)
        
        SpiWrite(spi,0x00,0x03)      #Переключаемся на 3 стр
        SpiWrite(spi,0x0D,0x00)      #Меняем DEC_RATE    0x10
        SpiWrite(spi,0x0C,0x00)      #Меняем DEC_RATE    0x99


        
        #Вывод данных в консоль
        print ("Температура:   ", "{:10.4f}".format(temp), " degС")
        print ("X гироскоп:   ", "{:10.4f}".format(xgyro), " deg/s")
        print ("Y гироскоп:   ", "{:10.4f}".format(ygyro), " deg/s")
        print ("Z гироскоп:   ", "{:10.4f}".format(zgyro), " deg/s")
        print ("X акселерометр:   ", "{:10.4f}".format(xacc), " mg")
        print ("Y акселерометр:   ", "{:10.4f}".format(yacc), " mg")
        print ("Z акселерометр:   ", "{:10.4f}".format(zacc), " mg")
        print('NULL_CNFG (должен быть = 0x70A на 3 стр) ', hex(SpiRead(spi,0x0E)))
        print('Decrate в 16-ричной системе ', hex(SpiRead(spi,0x0C)))
        print('Decrate в 10-чной системе  ', SpiRead(spi,0x0C))
        time.sleep(1)               #Задержка между обновлением данных

#Выход из цикла
except KeyboardInterrupt:           #Нажатие Ctrl+C
    spi.close()                     #Отключаем подключение шины SPI         
    GPIO.cleanup()

