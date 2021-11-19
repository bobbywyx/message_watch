import time
import utime
# from ssd1306 import SSD1306_I2C
from sh1106 import SH1106_I2C
import machine
from machine import Pin, UART, I2C, PWM, ADC, WDT
# from main_1 import V
import _thread as threading  # 因为micro python里面没有threading库  已经写好的class直接套用_thread
import framebuf
import json
import esp32
uart1 = UART(2, baudrate=115200, tx=17, rx=16)

uart1_power_pin = Pin(19, Pin.OUT)
uart1_power_pin.value(0)
print('3.3 to gnd in 5 secs')
lora_md0=Pin(4,Pin.OUT)

lora_md0.value(1)
uart1_power_pin.value(0)

time.sleep(4)
print('stop!!!! in 1sec')
time.sleep(1.5)
uart1_power_pin.value(1)
time.sleep(0.5)

#lora_md0.value(0)

count=0
print('starting')
while True:
    print('\n\n===============CNT {}==============='.format(count))

    # 发送一条消息
    print('Send: {}'.format('hello {}\n'.format(count)))
    print('Send Byte :') # 发送字节数
    # uartusb.write('hello {}\n'.format(count))
    utime.sleep_ms(10)
    
    if uart1.any():
        # 如果有数据 读入一行数据返回数据为字节类型
        # 例如  b'hello 1\n'
        bin_data = uart1.readline()
        # 将手到的信息打印在终端
        print('Echo Byte: {}'.format(bin_data))

        # 将字节数据转换为字符串 字节默认为UTF-8编码
        print('Echo String: {}'.format(bin_data.decode()))
    # 计数器+1
    bin_data = input('input by user:')
    print('usb read:',bin_data)
    uart1.write(bytearray(bin_data))
    count += 1
    print('---------------------------------------')