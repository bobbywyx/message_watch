import time
import utime
import framebuf
from ssd1306 import SSD1306_I2C
from machine import Pin, UART, I2C
import _thread as threading  # 因为micro python里面没有threading库  已经写好的class直接套用_thread

# config

WIDTH = 128
HEIGHT = 64

i2c = I2C(0)  # Init I2C using I2C0 defaults,SCL=Pin(GP9), SDA=Pin(GP8), freq=400000
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)  # Init oled display
oled.poweron()
oled.contrast(1)
oled.fill(0)

lora_addr = "00"
lora_tul = "00"
device_name = "wyx"

state_led_pin = Pin(25, Pin.OUT)
state_led_pin.value(0)

uart1 = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
uart1_power_pin = Pin(22, Pin.OUT)

back_button = Pin(5, Pin.IN, Pin.PULL_UP)
navi_button = Pin(4, Pin.IN, Pin.PULL_UP)
enter_button = Pin(3, Pin.IN, Pin.PULL_UP)

# in built message
in_built_message = (
    ('reply', 'yes', 'no', 'probably', "I don't know", "Not exactly", "Of course", 'not yet',
     'already have', 'thanks'),

    ('questions', 'Where r u', 'Where is ls', 'Where is ry', 'Where is wyx',
     'go to where', 'Where shall we meet',
     "R u ok", "Is classroom safe", "Is dormitory safe", "R u safe",
     ),  # question 发送会自动在结尾加上 ？

    ('location', 'classroom', 'dormitory', 'xiao mai bu', 'canteen', 'west canteen',
     'school gate', 'office', 'playground', 'gym', '1f', '2f', '3f', '4f', '5f',
     'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'),

    ('meal', "have breakfast yet?", "have lunch yet?",
     "have dinner yet?", "have night snack yet?",
     'go breakfast', 'go dinner', 'go lunch', 'go night snack',
     'queue for me', 'bring me sth to eat', 'bring me sth to drink',
     'do u want me to bring sth for u?'),

    ('suggestion', 'go to canteen', 'go to class', 'go to dormitory', 'go to office',
     'go to playground', 'go to gym', 'go breakfast', 'go dinner', 'go lunch', 'go night snack',
     ),  # suggestion 发送时会自动在 前面加上 what about 后面加上？

    ('demand', 'go with me', 'come to', 'go to', 'take ry go to', 'take wyx go to', 'take ls go to',
     'tell ry go to', 'tell wyx go to', 'tell ls go to'),

    ('state', 'hungry', 'stomach ache', 'head ache', 'sleepy', 'going shower',),

    ('dom-related',)
)


# menus
menu_watch = ('update time', )
menu_message = ('All', 'ls', 'ry', 'settings',)
menu_settings = ('oled contrast', 'sound', 'move', 'server test')
menu_chat = ('send', 'record',)


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
        uart1_power_pin.value(0)
    elif stat == 1:
        uart1_power_pin.value(1)


def battery_power():
    voltage = 2.9
    return voltage


def removing_joggle(old = utime.ticks_ms()):
    new = utime.ticks_ms()
    # print(utime.ticks_diff(old,new))
    if utime.ticks_diff(old,new) >=-200 and utime.ticks_diff(old,new) <1000:
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
        self.array = None  #menu模式的指针
        self.name = name   #自己的设备名称
        self.rxData = bytes()
        self.txData = b'hello world\n\r'
        self.target = None  #聊天对象
        self.time_start = int(time.time())
        self.rxMessage = ''
        self.real_time_delta = 1628006691 - time.time() + 28800  # 28800是+8时区
        self.father_dir = None
        self.working_menu = None
        self.ticks = utime.ticks_ms()
        self.oled_element = [None, None, None, False, None,
                             False, False, False, False, None,None]
                             # 'headleft' 'headmid' 'headright' 'headdivide' 'highlighter'
                                #  'midlrchange' 'midtime' 'middate'  'middivide' 'midgfc' 'menu'

    def main(self):
        self.opt(0)
        while True:
            while self.state == "Low power":
                # print('lowpower mode')
                self.display_main()
                time.sleep(0.5)
                if battery_power() < 3:
                    self.state_led('warning')
                if self.delta_t(self.time_start) > 60:
                    self.time_start = time.time()
                    print('lowpower check message')
                    self.message('r')
                    if not self.rxMessage:
                        self.state_led('message')
            while self.state == "Watch":
                # print('watch mode')
                timenow = time.localtime(time.time() + self.real_time_delta)
                self.oled_element = [battery_power(), 'wyx', None, True, None,
                                     False, timenow, timenow, False, None, None]
                self.generator()
                self.display_main()
                time.sleep(0.1)
                # print(timenow)
            while self.state == "Message":
                self.oled_element = [battery_power(), 'wyx', None, True, None,
                                     False, None, None, False, None, None]
                self.array = 0
                self.state = 'Menu'
                self.working_menu = menu_message
                # 进入message模式会直接跳转到menu模式 同时配置menu模式所需参数
                self.father_dir = 'Watch'
                self.menu_page_scroll()
                # print('message mode')
                time.sleep(0.1)
            while self.state == 'Menu':
                # 进入menu之前要进行配置 包括father_dir  working_menu state  array提前归零
                # 配置menu对象 通常是list或者tuple  同时要配置oled_element
                # menu模式有单独的渲染逻辑
                self.oled_element[4] = self.array
                self.generator()
                self.display_main()
                print('mm')
                time.sleep(0.1)
            while self.state == 'Chat':
                # chat模式是特殊的模式  包括了menu模式 但在聊天室里不包括menu逻辑
                pass
                time
            time.sleep(0.1)
            print('home')

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
            oled.text(str(self.oled_element[0]),0,0)
        if self.oled_element[1]:
            # headmid
            oled.text(str(self.oled_element[1]),54,0)
        if self.oled_element[2]:
            # headright
            oled.text(str(self.oled_element[2]),108,0)
        if self.oled_element[3]:
            # headdivide
            oled.hline(0, 8, 128,1)
        if self.oled_element[4] or self.array == 0:
            # highlighter
            oled.hline(0,(self.array % 6)*9+9,128,1)
            oled.hline(0,(self.array % 6)*9+17,128,1)
        if self.oled_element[5]:
            # mdlrchange
            pass
        if self.oled_element[6]:
            # middate
            oled.text(str(self.oled_element[6][0:3]),18,56)
        if self.oled_element[7]:
            # midtime
            time = self.oled_element[7][3:6]
            oled.text(str(time),20,40)
        if self.oled_element[8]:
            # middivide
            pass
        if self.oled_element[9]:
            # midgfc
            pass
        if self.oled_element[10]:
            # menu
            for i in range(len(self.oled_element[10])):
                oled.text(str(self.oled_element[10][i]),4,10+9*i)

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

        self.opt(1)

    def opt_enter(self):

        if removing_joggle(self.ticks):
            print('opt enter')
            if self.state == "Low power":
                self.state = "Watch"
            elif self.state == "Message":
                pass
                # 在message停留的时间应该会相当短 不会用到enter操作
            elif self.state == "Watch":
                self.state = "Message"
            elif self.state == "Menu":


                if self.working_menu[self.array] == 'update time':
                    print(self.working_menu[self.array])
                    self.time_correction()

                elif self.working_menu[self.array] == 'settings':
                    self.oled_element = [battery_power(), 'wyx', None, True, None,
                                         False, None, None, False, None, None]
                    self.working_menu = menu_settings
                    self.array=0
                    self.father_dir = 'Message'
                    self.menu_page_scroll()
                    time.sleep(0.05)
                elif self.working_menu == menu_message:
                    print(self.working_menu[self.array])
                    self.state ='Chat'
                    self.target = self.working_menu[self.array]

                elif self.working_menu[self.array]=='server test':
                    print(self.working_menu[self.array])
                    self.server_test()

                #以下为次级目录的选项

        self.opt(1)

    def opt_navi(self):

        if removing_joggle(self.ticks):
            print('opt navi')
            if self.state == "Low power":
                pass
            elif self.state=='Menu':
                self.array +=1
                if self.array % 6 ==0:
                    self.menu_page_scroll()
                if self.array == len(self.working_menu):
                    self.array = 0
                    self.menu_page_scroll()
                self.oled_element[4] = self.array
            elif self.state == "Message":
                pass
                #在message停留的时间应该会相当短 不会用到navi操作
            elif self.state == 'Watch':
                self.state = 'Menu'
                self.working_menu = menu_watch
                self.oled_element = [battery_power(), 'wyx', None, True, None,
                                     False, None, None, False, None, None]
                self.father_dir = 'Watch'
                self.array = 0
                self.menu_page_scroll()

        self.opt(1)

    def menu_page_scroll(self):
        if len(self.working_menu)-self.array <= len(self.working_menu) % 6:
            # 此处逻辑判断是当array遍历到最后六项（可能不足六项的情况）避免超出元组范围
            self.oled_element[10] = self.working_menu[(self.array//6)*6:len(self.working_menu)]
        else:
            self.oled_element[10] = self.working_menu[(self.array // 6) * 6:(self.array // 6+1) * 6]



    def display_main(self):

        if self.state == "Low power":
            oled.poweroff()
        else:
            oled.poweron()
            if self.state == "Watch":
                oled.show()
            elif self.state == 'Menu':
                oled.show()
            elif self.state =='Chat':
                oled.show()

    def message(self, opt):
        lora_power(1)
        if opt == 's':
            uart1.write(self.txData)
        elif opt == 'r':
            self.rxData = bytes()

            while uart1.any() > 0:
                self.rxData += uart1.read(1)
            time.sleep(0.001)
            self.rxMessage = self.rxData.decode('utf-8')
        else:
            print('message send option error')

    def delta_t(self, start_time):
        return time.time() - start_time

    def server_test(self):
        self.txData = b'test'
        self.message('s')
        time.sleep(0.1)
        self.message('r')
        if self.rxMessage:
            return True
        else:
            return False
    def time_correction(self):
        self.txData = b'check time'
        self.message('s')
        time.sleep(0.1)
        self.message('r')
        self.real_time_delta = float(self.rxMessage) - time.time()

    def state_led(self, stat):
        if stat == 'idle':
            state_led_pin.value(0)
        elif stat == 'warning':
            state_led_pin.value(1)
        elif stat == 'message':
            state_led_pin.value(1)
            time.sleep(0.1)
            state_led_pin.value(0)
            time.sleep(0.1)


if __name__ == '__main__':
    watch = Watch()
    watch.main()
