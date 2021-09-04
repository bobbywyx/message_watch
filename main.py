import time
import utime
# from ssd1306 import SSD1306_I2C
from sh1106 import SH1106_I2C
import machine
from machine import Pin, UART, I2C, PWM, ADC,WDT
# from main_1 import V
import _thread as threading  # 因为micro python里面没有threading库  已经写好的class直接套用_thread
import framebuf
# import network



# import gc

# wdt =WDT(timeout=100000)
# wdt.feed()
# config

WIDTH = 128
HEIGHT = 64

uart1 = UART(2, baudrate=9600, tx=12, rx=13)
uart1_power_pin = Pin(19, Pin.OUT)

i2c = machine.SoftI2C(scl=machine.Pin(22), sda=machine.Pin(21),)
# old on rp2040    i2c = I2C(0)  # Init I2C using I2C0 defaults,SCL=Pin(GP9), SDA=Pin(GP8), freq=400000
# oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)  # Init oled display
oled = SH1106_I2C(WIDTH, HEIGHT, i2c,)  # Init oled display

oled.flip(2)
oled.poweron()
oled.fill(0)
oledcontrast = 3
oled.contrast(int(oledcontrast * 25.2) + 1)
chat_record = {'All': [['ls:', 'OK', '8-14,18:18'], ['wyx:', 'OK', '8-14,18:19'], ['ry:', 'OK', '8-14,18:20'],
                       ['ry:', 'OK', '8-14,18:21'], ['ry:', 'OK', '8-14,18:23'], ['ry:', 'OK', '8-14,18:25'],
                       ['ry:', 'OK13', '8-14,18:20']],
               'ls': [['ls:', 'OK', '8-14,18:18']],
               'ry': []}

server_addr = b'11'
lora_addr = b'00'
lora_tul = b'00'
device_name = "wyx"

state_led_pin = Pin(11, Pin.OUT)
state_led_pin.value(0)
state_led = 0



back_button = Pin(14, Pin.IN, Pin.PULL_UP)
navi_button = Pin(13, Pin.IN, Pin.PULL_UP)
enter_button = Pin(12, Pin.IN, Pin.PULL_UP)

voltage_sense = ADC(9)
conversion_factor = 3.3 / (65535)

'''
motorpin = Pin(22)
timer2 = Timer(2,freq=100)
motor1 = timer2.channel(1,Timer.PWM,pin=motorpin)
motor1.pulse_width_percent(10)
'''
motorpin = PWM(Pin(23))
motorpin.freq(100)
motorpin.duty_u16(30000)
sound = 3
move = 3

frame_counter = None

led_notice_flag = 0
led_state_flag = 0
# in built message
in_built_message_menu = ('reply', 'questions', 'location', 'meal', 'suggestion', 'demand', 'state', 'dom-related',
                         'combine message',)
in_built_message = (
    # reply
    ('yes', 'no', 'probably', "I don't know", "Not exactly", "Of course", 'not yet',
     'already have', 'thanks'),
    # questions
    ('Where r u?', 'Where is ls?', 'Where is ry?', 'Where is wyx?',
     'go to where?', 'Where shall we meet?',
     "R u ok?", "Is classroom safe?", "Is dormitory safe?", "R u safe?",
     ),
    # location
    ('classroom', 'dormitory', 'xiao mai bu', 'canteen', 'west canteen',
     'school gate', 'office', 'playground', 'gym', '1f', '2f', '3f', '4f', '5f',
     'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'),
    # meal
    ("have breakfast yet?", "have lunch yet?",
     "have dinner yet?", "have night snack yet?",
     'go breakfast', 'go dinner', 'go lunch', 'go night snack',
     'queue for me', 'bring me sth to eat', 'bring me sth to drink',
     'do u want me to bring sth for u?'),
    # suggestion
    ('why not go to canteen?', 'why not go to class?', 'why not go to dormitory?', 'why not go to office?',
     'why not go to playground?', 'why not go to gym?', 'why not go breakfast?', 'why not go dinner?',
     'why not go lunch?',
     'why not go to have night snack?',
     ),  # suggestion 发送时会自动在 前面加上 what about 后面加上？
    # demand
    ('go with me', 'come to', 'go to', 'take ry go to', 'take wyx go to', 'take ls go to',
     'tell ry go to', 'tell wyx go to', 'tell ls go to'),
    # state
    ('hungry', 'stomach ache', 'head ache', 'sleepy', 'going shower',),
    # dom-related
    ('some one using bathroom', 'teacher here', 'I will go sleeping', 'I will use bathroom'),
    # combine message
    ('ls,...', 'ry...', 'everyone...', 'I,wyx,...',),
)

# menus
menu_watch = ('update time','watch video')
menu_message = ('All', 'ls', 'ry', 'settings',)
menu_settings = ('oled contrast', 'sound', 'move', 'server test')
menu_chat = ('send', 'record', 'load')

direct_func_names = ('update_time','server_test', 'send', 'record', 'load')  # 函数本身和显示函数名只有空格和下划线差距的函数
other_func = ('watch_video')
day_week = ('Mon', "Tue", "Wed", "Thur", "Fri", "Sat", "Sun")

'''
def wifi_connect():
    wifi_led = state_led_pin  # 板载指示灯初始化
    wlan = network.WLAN(network.STA_IF)  # 以工作站 (wlan) 模式运行，需要创建一个工作站Wi-Fi接口的实例
    wlan.active(True)  # 在工作站对象上调用激活方法并以True作为输入值传递来激活网络接口
    start_time = time.time()  # 记录开始时间

    if not wlan.isconnected():  # 如果尚未联网成功
        print("当前无线未联网，正在连接中....")
        wlan.connect("110-0-11", "19921227")  # 无线网SSID、密码，开始联网
        while not wlan.isconnected():  # 如果还未连接成功，则LED灯闪烁提示
            wifi_led.value(1)
            time.sleep(1)
            wifi_led.value(1)
            time.sleep(1)
            print("正在尝试连接到wifi....")
            print(time.time())

            if time.time() - start_time > 15:  # 如果超过15秒还不行，就退出
                print("连接失败!!!无线网连接超过15秒，请检查无线网名称和密码是否正确..")
                oled.fill(0)
                oled.text('wifi not connected', 0, 0, 1)
                oled.show()
                time.sleep(1)
                break

    if wlan.isconnected():  # 如果联接成功
        oled.fill(0)
        oled.text('wifi connected', 0, 0, 1)
        oled.show()
        time.sleep(1)
        wifi_led.value(1)  # LED灯常亮
        IP_info = wlan.ifconfig()
        print("无线网已经连接，信息如下：")
        print("IP地址：" + IP_info[0])
        print("子网掩码：" + IP_info[1])
        print("网关：" + IP_info[2])
        print("DNS：" + IP_info[3])
'''

# 开始执行联网模块

class EventManager:
    def __init__(self):
        self._event_dict = {}

    def register_event_listener(self, event_title, method):
        if event_title in self._event_dict:
            methods_list = self._event_dict[event_title]
        else:
            methods_list = []
        methods_list.append(method)
        self._event_dict[event_title] = methods_list

    def del_event_listener(self, event_type, method):
        if event_type in self._event_dict:
            methods_set = self._event_dict[event_type]
            methods_set.discard(method)
            if len(methods_set) == 0:
                del self._event_dict[event_type]
            else:
                self._event_dict[event_type] = methods_set
        else:
            pass

    def broadcast_event(self, event_type, args=None, ):
        if args is None:
            args = ()
        if event_type not in self._event_dict:
            return 1
        methods_set = self._event_dict[event_type]
        for single_method in methods_set:
            t = threading.start_new_thread(single_method, args)

        return 0


def lora_power(stat):
    if stat == 0:
        uart1_power_pin.value(1)
    elif stat == 1:
        uart1_power_pin.value(0)
        # print('lora on')


def battery_power():
    voltage = voltage_sense.read_u16() * conversion_factor * 2
    return round(voltage, 2)


def removing_joggle(old=utime.ticks_ms()):
    new = utime.ticks_ms()
    # print(utime.ticks_diff(old,new))
    if utime.ticks_diff(old, new) >= -200 and utime.ticks_diff(old, new) < 1000:
        # print('removed joggle')
        return False
    else:
        # print('no joggle')
        return True


# system
class Watch:
    def __init__(self, state="Watch", addr=lora_addr, tul=lora_tul, name=device_name, ):
        self.state = state
        self.addr = addr
        self.tul = tul
        self.array = None  # menu模式的指针
        self.name = name  # 自己的设备名称
        self.rxData = bytes()
        self.txData = b'hello world\n\r'
        self.target = None  # 聊天对象
        self.time_start = int(time.time())
        self.rxMessage = ''
        self.real_time_delta = 1628931445 - time.time() + 28800  # 28800是+8时区
        self.father_dir = None
        self.working_menu = None
        self.ticks = utime.ticks_ms()
        self.message_choose_flag = 0
        self.is_connected = False
        self.text_scroll_flag = [0] * 6
        self.new_message_targets = ['All', 'ry']
        self.oled_element = [None, None, None, False, None,
                             False, False, False, False, None, None]
        self.target_other_func=None
        # 'headleft' 'headmid' 'headright' 'headdivide' 'highlighter'
        #  'midlrchange' 'midtime' 'middate'  'middivide' 'midgfc' 'menu'

    def main(self):
        self.opt(0)
        while True:
            while self.state == "Low power":
#                 wdt.feed()
                # print('lowpower mode')
                self.display_main()
                time.sleep(0.5)
                if battery_power() < 3:
                    self.state_led('warning')
                else:
                    self.state_led('idle')
                if self.delta_t(self.time_start) > 60:
                    self.time_start = time.time()
                    print('lowpower check message')
                    self.message('r')
                    if not self.rxMessage:
                        self.state_led('message')
            while self.state == "Watch":
#                 wdt.feed()
                # print('watch mode')
                timenow = time.localtime(time.time() + self.real_time_delta)
                self.oled_element = [battery_power(), 'wyx',
                                     day_week[time.localtime(time.time() + self.real_time_delta)[6]], True, None,
                                     False, timenow, timenow, False, None, None]
                self.generator()
                self.display_main()
                time.sleep(0.1)
                # print(timenow)
            while self.state == "Message":
#                 wdt.feed()
                self.oled_element = [battery_power(), 'wyx', None, True, None,
                                     False, None, None, False, None, None]
                if self.is_connected:
                    self.oled_element[2] = 'c'
                else:
                    self.oled_element[2] = 'n'

                self.array = 0
                self.state = 'Menu'
                self.working_menu = menu_message
                # 进入message模式会直接跳转到menu模式 同时配置menu模式所需参数
                self.father_dir = 'Watch'
                self.menu_page_scroll()
                # print('message mode')
                time.sleep(0.1)
                self.text_scroll_flag = [a + 1 for a in self.text_scroll_flag]
                lora_power(1)

            while self.state == 'Menu':
                wdt.feed()
                # 进入menu之前要进行配置 包括father_dir  working_menu state  array提前归零
                # 配置menu对象 通常是list或者tuple  同时要配置oled_element
                # menu模式有单独的渲染逻辑
                self.oled_element[4] = self.array
                self.menu_page_scroll()
                self.generator()
                self.display_main()
                time.sleep(0.1)
                self.text_scroll_flag = [a + 1 for a in self.text_scroll_flag]
            while self.state == 'Chat':
#                 wdt.feed()
                self.oled_element = [battery_power(), self.target, None, True, None,
                                     False, None, None, False, None, None]

                self.father_dir = "Message"
                self.message_page_scroll(chat_record[self.target][-6:])
                self.generator()
                self.display_main()
                # chat模式是特殊的模式  包括了menu模式 但在聊天室里不包括menu逻辑
                time.sleep(0.1)
                self.text_scroll_flag = [a + 1 for a in self.text_scroll_flag]
            while self.state == "Record":
#                 wdt.feed()
                self.oled_element = [battery_power(), self.target,
                                     str((len(chat_record[self.target]) + 2) // 3 - self.array) + '/' +
                                     str((len(chat_record[self.target]) + 2) // 3),
                                     True, None,
                                     False, None, None, False, None, None]
                self.message_page_scroll(chat_record[self.target])
                self.generator()
                self.display_main()
                time.sleep(0.1)
                self.text_scroll_flag = [a + 1 for a in self.text_scroll_flag]
            time.sleep(0.1)
            while self.state == 'Other':
#                 wdt.feed()
                #其他功能渲染模式
                # self.oled_element=[None, None, None, False, None,
                #              False, False, False, False, None, None]
                self.target_other_func()
                print('other state')



    def opt(self, od):
        if od == 0:
            back_button.irq(lambda pin: self.opt_back(), Pin.IRQ_FALLING)
            navi_button.irq(lambda pin: self.opt_navi(), Pin.IRQ_FALLING)
            enter_button.irq(lambda pin: self.opt_enter(), Pin.IRQ_FALLING)

        elif od == 1:
            self.ticks = utime.ticks_ms()

    def generator(self):
        oled.fill(0)
        if self.oled_element[0]:
            # headleft
            oled.text(str(self.oled_element[0]), 0, 0)
        if self.oled_element[1]:
            # headmid
            oled.text(str(self.oled_element[1]), 63 - len(str(self.oled_element[1])) * 4, 0)
        if self.oled_element[2]:
            # headright

            oled.text(str(self.oled_element[2]), 127 - len(self.oled_element[2]) * 8, 0)
        if self.oled_element[3]:
            # headdivide
            oled.hline(0, 8, 128, 1)
        if self.oled_element[4] is not None:
            # highlighter
            # oled.hline(0, (self.array % 6) * 9 + 9, 128, 1)
            # oled.hline(0, (self.array % 6) * 9 + 17, 128, 1)
            oled.rect(0, (self.array % 6) * 9 + 9, 128, 10, 1)
            if self.working_menu == menu_message and self.new_message_targets is not []:
                for mm in self.new_message_targets:
                    oled.fill_rect(2, menu_message.index(mm) * 9 + 13, 2, 2, 1)

        if self.oled_element[5]:
            # mdlrchange
            pass
        if self.oled_element[6]:
            # middate
            oled.text(str(self.oled_element[6][0:3]), 18, 56)
        if self.oled_element[7]:
            # midtime
            time = self.oled_element[7][3:6]
            oled.text(str(time), 20, 40)
        if self.oled_element[8]:
            # middivide
            pass
        if self.oled_element[9]:
            # midgfc
            pass
        if self.oled_element[10]:
            # menu
            for i in range(len(self.oled_element[10])):
                oled.text(self.text_scroller(str(self.oled_element[10][i]), i), 4, 10 + 9 * i)

    def opt_back(self):
        if removing_joggle(self.ticks):
            print('opt back')
            if self.state == "Low power":
                pass
            elif self.state == "Message":
                # self.state = 'Watch'
                # 在message停留的时间应该会相当短 不会用到back操作
                pass
            elif self.state == "Watch":
                self.state = 'Low power'
            elif self.state == 'Chat':
                self.state = 'Message'
            elif self.state == 'Menu':
                if self.father_dir == 'Watch':
                    self.state = 'Watch'
                    self.working_menu = None
                    self.father_dir = None
                    self.array = None
                elif self.father_dir == 'Message':
                    self.state = 'Message'
                elif self.message_choose_flag == 1:
                    self.working_menu = in_built_message_menu
                    self.array = 0
                    self.message_choose_flag = 0
                elif self.father_dir == 'Chat':
                    self.state = 'Chat'
                    self.array = -1

            elif self.state == 'Column':
                self.state = 'Message'
            elif self.state == 'Record':
                self.state = 'Menu'
                self.array = 0
                self.working_menu = menu_chat
                self.menu_page_scroll()
            elif self.state=='Other':
                self.state= self.father_dir
        self.opt(1)

    def opt_enter(self):

        if removing_joggle(self.ticks):
            # print('opt enter')
            if self.state == "Low power":
                self.state = "Watch"
                self.state_led(0)
            elif self.state == "Message":
                pass
                # 在message停留的时间应该会相当短 不会用到enter操作
            elif self.state == "Watch":
                self.state = "Message"

            elif self.state == 'Column':
                self.opt_back()

            elif self.state == "Menu":

                target = self.working_menu[self.array]

                if target in ('oled contrast', 'sound', 'move'):
                    self.column()

                elif self.message_choose_flag == 1:
                    self.txData = bytearray(server_addr + b'/' + lora_tul + b'/' +
                                            self.name.encode() + b'/' + self.target.encode() + b'/'
                                            + self.working_menu[self.array].encode())
                    self.message('s')
                    self.opt_back()

                elif target in in_built_message_menu:
                    self.working_menu = in_built_message[self.array]
                    self.menu_page_scroll()
                    self.array = 0
                    self.message_choose_flag = 1

                elif target.replace(' ', '_') in direct_func_names:
                    print('direct func')
                    # eval('watch.' + target.replace(' ', '_') + '()')
                    getattr(self,target.replace(' ', '_'))()
                    # eval('watch.opt_back()')

                elif target.replace(' ', '_') in other_func:
                    print('other func')
                    # eval('watch.' + target.replace(' ', '_') + '()')
                    self.target_other_func = getattr(self,target.replace(' ', '_'))
                    self.state='Other'

                elif target == 'settings':
                    self.oled_element = [battery_power(), 'config', None, True, None,
                                         False, None, None, False, None, None]
                    self.working_menu = menu_settings
                    self.array = 0
                    self.father_dir = 'Message'
                    self.menu_page_scroll()
                    time.sleep(0.05)

                elif self.working_menu == menu_message:
                    # 在经过以上判断以后能进入这个if肯定是选中的某个聊天对象所以进入chat模式
                    self.state = 'Chat'
                    self.target = self.working_menu[self.array]
                    if self.target in self.new_message_targets:
                        self.new_message_targets.remove(self.target)
                    self.array = -1

        self.opt(1)

    def opt_navi(self):

        if removing_joggle(self.ticks):
            # print(gc.mem_free())
            # print('opt navi')
            self.text_scroll_flag = [0] * 6
            if self.state == "Low power":
                pass
            elif self.state == 'Menu':
                self.array += 1
                if self.array % 6 == 0:
                    self.menu_page_scroll()
                if self.array == len(self.working_menu):
                    self.array = 0
                    self.menu_page_scroll()
                self.oled_element[4] = self.array
            elif self.state == "Message":
                pass
                # 在message停留的时间应该会相当短 不会用到navi操作
            elif self.state == "Column":
                self.column()
            elif self.state == 'Watch':
                self.state = 'Menu'
                self.working_menu = menu_watch
                self.oled_element = [battery_power(), 'wyx', None, True, None,
                                     False, None, None, False, None, None]
                self.father_dir = 'Watch'
                self.array = 0
                self.menu_page_scroll()
            elif self.state == "Chat":
                self.state = 'Menu'
                self.working_menu = menu_chat
                self.father_dir = 'Chat'
                self.array += 1
                self.menu_page_scroll()
            elif self.state == "Record":
                self.array += 1
        self.opt(1)

    def menu_page_scroll(self):
        if len(self.working_menu) - self.array <= len(self.working_menu) % 6:
            # 此处逻辑判断是当array遍历到最后六项（可能不足六项的情况）避免超出元组范围
            self.oled_element[10] = self.working_menu[(self.array // 6) * 6:len(self.working_menu)]
        else:
            self.oled_element[10] = self.working_menu[(self.array // 6) * 6:(self.array // 6 + 1) * 6]

    def message_page_scroll(self, record_list):
        if len(record_list) == 0:
            self.oled_element[10] = ('Not loaded', 'or no record')
        elif self.state == 'Record':
            # record 模式下第一行内容，第二行具体时间
            # 所以实际上只能一次显示三条 要把原来的6都改成3
            dplist = []
            lc = (len(record_list) + 2) // 3
            if self.array == lc:
                self.array = 0
            elif self.array == lc - 1:
                self.oled_element[10] = record_list[0:4]
                for i in self.oled_element[10]:
                    dplist.append(i[0] + i[1])
                    dplist.append(i[2])
                self.oled_element[10] = dplist
            else:
                self.oled_element[10] = record_list[(-self.array * 3 - 3):len(record_list) - self.array * 3]
                for i in self.oled_element[10]:
                    dplist.append(i[0] + i[1])
                    dplist.append(i[2])
                self.oled_element[10] = dplist

        else:
            dplist = []
            lc = (len(record_list) + 5) // 6
            if self.array == lc:
                self.array = 0
            elif self.array == lc - 1:
                self.oled_element[10] = record_list[0:7]
                for i in self.oled_element[10]:
                    dplist.append(i[0] + i[1])
                self.oled_element[10] = dplist
            else:
                self.oled_element[10] = record_list[(-self.array * 6 - 6):len(record_list) - self.array * 6]
                for i in self.oled_element[10]:
                    dplist.append(i[0] + i[1])
                self.oled_element[10] = dplist

    def display_main(self):

        if self.state == "Low power":
            oled.poweroff()

        else:
            oled.poweron()
            oled.contrast(int(oledcontrast * 25.2) + 1)
            oled.show()

    def message(self, opt):
        lora_power(1)
        if opt == 's':
            uart1.write(bytearray(self.txData))
            print('sending uart1 lora:', self.txData)
        elif opt == 'r':
            # print('try to receive uart1')
            self.rxData = bytes()
            while uart1.any() > 0:
                self.rxData += uart1.read(1)
            time.sleep(0.001)
            if self.rxData:
                self.is_connected = True
            else:
                self.is_connected = False

            self.rxMessage = self.rxData.decode('utf-8')
        else:
            print('message send option error')

    def delta_t(self, start_time):
        return time.time() - start_time

    # direct func name
    def server_test(self):
        print('try to connect')
        self.txData = bytearray(server_addr + b'/' + lora_tul + b'/' +
                                self.name.encode() + b'/SA_test')
        self.message('s')
        time.sleep(0.1)
        self.message('r')
        if self.rxMessage:
            return True
        else:
            return False


    def watch_video(self):
        global frame_counter
        if frame_counter is None:
            frame_counter = 0
        else:frame_counter+=1
        self.state='Other'
        self.father_dir='Watch'
        if frame_counter<315:
            dirt = '/buffers/' + str(frame_counter *12) + '.pbm'
            with open(dirt, 'rb') as f:
                f.readline()
                f.readline()
                data = bytearray(f.read())
                fbuf = framebuf.FrameBuffer(data, 128, 64, framebuf.MONO_HLSB)
                oled.fill(0)
                oled.blit(fbuf, 0, 0)
                oled.show()
                del fbuf
                time.sleep(0.35)
        else:
            frame_counter = None
            self.state='Watch'


    def update_time(self):
        print('update_time')
        self.txData = bytearray(server_addr + b'/' + lora_tul + b'/' +
                                self.name.encode() + b'/SA_updatetime')
        self.message('s')
        time.sleep(0.1)
        self.message('r')
        if self.rxMessage:
            self.real_time_delta = float(self.rxMessage) - time.time()
        else:
            oled.fill(0)
            oled.text('fail to update', 0, 31)
            oled.show()
            time.sleep(1)
            self.opt_back()

    def wifi_time(self):
        pass
        '''
        # micropython 校时程序  (注意，必须先联网成功后，才能校时成功！！！)
        wifi_connect()

        print("同步前本地时间：%s" %str(time.localtime()))
        ntptime.NTP_DELTA = 3155644800    # 设置  UTC+8偏移时间（秒），不设置就是UTC0
        ntptime.host = 'ntp1.aliyun.com'  # 可选ntp服务器为阿里云服务器，默认是"pool.ntp.org"
        ntptime.settime()                 # 修改设备时间,到这就已经设置好了
        print("同步后本地时间：%s" %str(time.localtime()))
        self.real_time_delta = 0
        '''

    def send(self):
        # chat状态下的发送函数
        self.oled_element = [battery_power(), self.target, None, True, None,
                             False, None, None, False, None, None]
        self.working_menu = in_built_message_menu
        self.father_dir = "Chat"
        self.state = 'Menu'

    def record(self):
        # chat状态下的查看历史记录函数
        print('record')
        self.array = 0
        self.message_page_scroll(chat_record[self.target])
        self.state = 'Record'

    def load(self):
        # chat状态下的加载历史记录函数
        print('load start')
        self.time_start = time.time()
        self.txData = bytearray(server_addr + b'/' + lora_tul + b'/' +
                                self.name.encode() + b'/SA_load' + b'/' +
                                self.target.encode())
        self.rxMessage = ''
        self.message('s')
        while not self.rxMessage and time.time() - self.time_start <= 5:
            time.sleep(0.01)
            self.message('r')
        if self.rxData:
            chat_record[self.target] = eval(self.rxData.decode())
        self.opt_back()
        print('load end')

    def state_led(self, stat):
        global led_notice_flag, led_state_flag
        if stat == 'idle' or not stat:
            state_led_pin.value(0)
            # led_state_flag=0
        elif stat == 'warning' or stat == 1:
            state_led_pin.value(1)
            # led_state_flag=1
        elif stat == 'message':
            led_notice_flag = 1
        if led_notice_flag == 1:
            state_led_pin.value(1 - led_state_flag)
            led_state_flag = 1 - led_state_flag
            time.sleep(0.1)

    def column(self):
        self.state = 'Column'
        globals()[self.working_menu[self.array].replace(' ', '')] += 1
        if globals()[self.working_menu[self.array].replace(' ', '')] == 6: globals()[
            self.working_menu[self.array].replace(' ', '')] = 0
        oled.fill(0)
        oled.text(str(globals()[self.working_menu[self.array].replace(' ', '')]), 60, 30, )
        oled.contrast(int(oledcontrast * 25.2) + 1)
        oled.show()

    def text_scroller(self, text, i):
        # 能滚动过长字幕的函数，目前只搭配oled元素10使用，所以第二个参数i很重要，为了每一条字幕单独滚动
        if len(text) > 16:
            st = (self.text_scroll_flag[i] // 4) % len(text)
            if len(text) - st < 12:
                st = 0
                self.text_scroll_flag[i] = 0
            # print('text scroller working:',text[st:])
            return text[st:]
        else:
            # print('dont need to scroll')
            return text


if __name__ == '__main__':
    lora_power(0)
    watch = Watch()
    watch.main()
