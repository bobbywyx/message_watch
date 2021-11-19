import time
import utime
# from ssd1306 import SSD1306_I2C
from sh1106 import SH1106_I2C
from machine import Pin, UART, I2C, PWM, ADC
import json
import framebuf

class Watch:
    def __init__(self, state, addr, tul, name, oled):
        self.state = "Watch"
        self.addr = addr
        self.tul = tul
        self.array = None  # menu模式的指针
        self.name = name  # 自己的设备名称
        self.rxData = bytes()
        self.txData = b'hello world\n\r'
        self.target = None  # 聊天对象
        self.oled = oled

        self.rxMessage = ''
        self.real_time_delta = 1631412287 - time.time() + 28800 - 946684800  # 28800是+8时区 946684800是2000年和1970年时间戳差值
        self.father_dir = None
        self.working_menu = None
        self.ticks = utime.ticks_ms()
        self.message_choose_flag = 0
        self.is_connected = False
        self.text_scroll_flag = [0] * 6
        self.new_message_targets = ['All', 'ry']
        self.oled_element = [None, None, None, False, None,
                             False, False, False, False, None, None]
        self.fonts = None
        self.target_other_func = None
        self.re_enter = 0
        self.opt_navi_is_pressed = 0
        self.opt_enter_is_pressed = 0
        # self.rtc = RTC()

        # self.rtc.init((2021,10,10,1,0,0,0,0))
        self.time_start = int(time.time())
        # 'headleft' 'headmid' 'headright' 'headdivide' 'highlighter'
        #  'midlrchange' 'midtime' 'middate'  'middivide' 'midgfc' 'menu'

    def main(self):
        self.opt(0)
        while True:
            while self.state == "Low power":
                # wdt.feed()
                # print('lowpower mode')
                self.display_main()
                # print('sleeping(idle)')
                # rtc.alarm(rtc.ALARM0, 10000)
                time.sleep(0.5)
                # machine.lightsleep()

                # print('awake now')
                if stateled == 0:
                    self.state_led('idle')
                    if self.delta_t(self.time_start) > 60:
                        self.time_start = time.time()
                        print('lowpower check message')
                        self.message('r')
                else:
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
                print('delta t:', self.delta_t(self.time_start))
                if self.delta_t(self.time_start) > 60:
                    self.time_start = time.time()
                    self.state = 'Low power'

                if self.fonts is None:
                    print('load fonts')
                    # 加载字库
                    self.fonts = []
                    for ff in range(10):
                        dirt = '/time_fonts/' + str(ff)
                        with open(dirt, 'rb') as f:
                            data = bytearray(json.loads(f.read()))
                            if self.fonts is None:
                                self.fonts = []
                            else:
                                self.fonts.append(framebuf.FrameBuffer(data, 16, 32, framebuf.MONO_HLSB))
                    dirt = '/time_fonts/colon'
                    with open(dirt, 'rb') as f:
                        data = bytearray(json.loads(f.read()))
                        if self.fonts is None:
                            self.fonts = []
                        else:
                            self.fonts.append(framebuf.FrameBuffer(data, 16, 32, framebuf.MONO_HLSB))

                timenow = time.localtime(time.time() + self.real_time_delta)
                # timenow = time.localtime(time.time())
                self.oled_element = [battery_power(), self.name,
                                     day_week[time.localtime(time.time() + self.real_time_delta)[6]], True, None,
                                     False, timenow, timenow, False, None, None]
                self.generator()
                self.display_main()
                time.sleep(0.2)
                # print('rtc test:', rtc.datetime())
                # print('after check time.time:',time.localtime(time.time()))
                # print(timenow)
            while self.state == "Message":
                #                 wdt.feed()
                self.oled_element = [battery_power(), self.name, None, True, None,
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
                self.oled_element = [battery_power(), self.target, None, True, None,
                                     False, None, None, False, None, None]

                self.father_dir = "Menu"
                self.working_menu = menu_message  # 从chat退出就直接回到message
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
                # 其他功能渲染模式
                # self.oled_element=[None, None, None, False, None,
                #              False, False, False, False, None, None]
                print('if re enterred', self.re_enter)
                self.target_other_func()
                self.re_enter = 0
                print('other state')

    def opt(self, od):
        if od == 0:
            back_button.irq(lambda pin: self.opt_back(), Pin.IRQ_FALLING)
            navi_button.irq(lambda pin: self.opt_navi(), Pin.IRQ_FALLING)
            enter_button.irq(lambda pin: self.opt_enter(), Pin.IRQ_FALLING)
            esp32.wake_on_ext0(pin=enter_button, level=esp32.WAKEUP_ALL_LOW)

            # rtc.irq(trigger=rtc.ALARM0, wake=esp32.WAKEUP_ALL_LOW)


        elif od == 1:
            self.ticks = utime.ticks_ms()

    def generator(self):
        self.oled.fill(0)
        if self.oled_element[0]:
            # headleft
            self.oled.text(str(self.oled_element[0]), 0, 0)
        if self.oled_element[1]:
            # headmid
            self.oled.text(str(self.oled_element[1]), 63 - len(str(self.oled_element[1])) * 4, 0)
        if self.oled_element[2]:
            # headright

            self.oled.text(str(self.oled_element[2]), 127 - len(self.oled_element[2]) * 8, 0)
        if self.oled_element[3]:
            # headdivide
            self.oled.hline(0, 8, 128, 1)
        if self.oled_element[4] is not None:
            # highlighter
            # self.oled.hline(0, (self.array % 6) * 9 + 9, 128, 1)
            # self.oled.hline(0, (self.array % 6) * 9 + 17, 128, 1)
            self.oled.rect(0, (self.array % 6) * 9 + 9, 128, 10, 1)
            if self.working_menu == menu_message and self.new_message_targets is not []:
                for mm in self.new_message_targets:
                    self.oled.fill_rect(2, menu_message.index(mm) * 9 + 13, 2, 2, 1)

        if self.oled_element[5]:
            # mdlrchange
            pass
        if self.oled_element[6]:
            # middate
            self.oled.text(str(self.oled_element[6][0:3]), 18, 56)
        if self.oled_element[7] and self.fonts:
            # midtime
            time = self.oled_element[7][3:6]

            # dirt = '/time_fonts/colon'
            # with open(dirt, 'rb') as f:
            #     data = bytearray(json.loads(f.read()))
            if self.fonts:
                self.oled.blit(framebuf.FrameBuffer(self.fonts[10], 16, 32, framebuf.MONO_HLSB), 35, 10)
                self.oled.blit(framebuf.FrameBuffer(self.fonts[10], 16, 32, framebuf.MONO_HLSB), 83, 10)
            for tt in range(3):
                # first digit

                # dirt = '/time_fonts/' + str(time[tt] // 10)
                # with open(dirt, 'r') as f:
                # print(f.read().decode())
                # data = bytearray(json.loads(f.read()))

                if self.fonts: self.oled.blit(framebuf.FrameBuffer(self.fonts[time[tt] // 10], 16, 32, framebuf.MONO_HLSB),
                                         48 * tt, 13)

                # second digit
                # dirt = '/time_fonts/' + str(time[tt] % 10)
                # with open(dirt, 'rb') as f:
                #     data = bytearray(json.loads(f.read()))

                if self.fonts: self.oled.blit(framebuf.FrameBuffer(self.fonts[time[tt] % 10], 16, 32, framebuf.MONO_HLSB),
                                         16 + 48 * tt, 13)

            # del data,
        if self.oled_element[8]:
            # middivide
            pass
        if self.oled_element[9]:
            # midgfc
            pass
        if self.oled_element[10]:
            # menu
            for i in range(len(self.oled_element[10])):
                self.oled.text(self.text_scroller(str(self.oled_element[10][i]), i), 4, 10 + 9 * i)

    def opt_back(self):
        global led_notice_flag
        if removing_joggle(self.ticks):
            print('opt back')
            if self.state == "Low power":
                pass
            elif self.state == "Message":
                # self.state = 'Watch'
                # 在message停留的时间应该会相当短 不会用到back操作
                pass
            elif self.state == "Watch":
                # self.fonts = None
                time.sleep(0.1)
                self.state = 'Low power'
                led_notice_flag = 0
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
                elif type(self.father_dir) == type(menu_watch):
                    self.state = 'Menu'
                    self.working_menu = self.father_dir
                    self.array = 0



            elif self.state == 'Column':
                self.state = 'Message'
            elif self.state == 'Record':
                self.state = 'Menu'
                self.array = 0
                self.working_menu = menu_chat
                self.menu_page_scroll()
            elif self.state == 'Other':
                self.state = self.father_dir
                self.re_enter = 1
        self.opt(1)

    def opt_enter(self):

        if removing_joggle(self.ticks):
            # print('opt enter')
            if self.state == "Low power":
                self.state = "Watch"
                self.time_start = time.time()
                self.state_led(0)
            elif self.state == "Message":
                pass
                # 在message停留的时间应该会相当短 不会用到enter操作
            elif self.state == "Watch":
                # self.fonts = None
                time.sleep(0.1)

                self.state = "Message"

            elif self.state == 'Column':
                self.opt_back()

            elif self.state == "Menu":

                target = self.working_menu[self.array]

                if target in ('oled contrast', 'sound', 'move', 'state led'):
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
                    getattr(self, target.replace(' ', '_'))()
                    # eval('watch.opt_back()')

                elif target.replace(' ', '_') in other_func:
                    print('other func')
                    # eval('watch.' + target.replace(' ', '_') + '()')
                    self.target_other_func = getattr(self, target.replace(' ', '_'))
                    self.state = 'Other'
                    # 上一行禁用掉是因为避免出现other不知道自己退出重新进入，所以
                    # 所有other函数麻烦自己重新定义一下state
                    # 重新写一下，因为不进入其他模式会有奇怪的函数无法运行bug，所以还是启用上一行
                    # 为了解决不知道重新进入的问题，请使用self.re_enter来判断，0是没有，1是有重新进入
                    # 不过从other func退出时，系统会自动把re_enter归为1，所以请other func自己判断吧
                elif target == 'settings':
                    self.oled_element = [battery_power(), 'config', None, True, None,
                                         False, None, None, False, None, None]
                    self.working_menu = menu_settings
                    self.array = 0
                    self.father_dir = 'Message'
                    self.menu_page_scroll()
                    time.sleep(0.05)

                elif target == 'info':
                    self.oled_element = [battery_power(), 'info', None, True, None,
                                         False, None, None, False, None, None]
                    self.working_menu = menu_info
                    self.array = 0
                    self.father_dir = menu_settings
                    self.menu_page_scroll()
                    time.sleep(0.05)


                elif self.working_menu == menu_message:
                    # 在经过以上判断以后能进入这个if肯定是选中的某个聊天对象所以进入chat模式
                    self.state = 'Chat'
                    self.target = self.working_menu[self.array]
                    if self.target in self.new_message_targets:
                        self.new_message_targets.remove(self.target)
                    self.array = -1
            elif self.state == 'Other':
                self.opt_enter_is_pressed = 1
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
                # self.fonts = None
                time.sleep(0.1)

                self.state = 'Menu'
                self.working_menu = menu_watch
                self.oled_element = [battery_power(), self.name, None, True, None,
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
            elif self.state == 'Other':
                self.opt_navi_is_pressed = 1
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
        # 几乎弃用状态，目前只有Low power模式关屏幕和调整亮度两个功能
        if self.state == "Low power":
            self.oled.poweroff()

        else:
            self.oled.poweron()
            self.oled.contrast(int(oledcontrast * 25.2) + 1)
            self.oled.show()

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
        elif frame_counter >= 280 and self.re_enter == 1:
            frame_counter = 0
        else:
            frame_counter += 1
        self.state = 'Other'
        self.father_dir = 'Watch'
        if frame_counter < 311:
            dirt = '/buffers/' + str(frame_counter * 12) + '.pbm'
            with open(dirt, 'rb') as f:
                f.readline()
                f.readline()
                data = bytearray(f.read())
                fbuf = framebuf.FrameBuffer(data, 128, 64, framebuf.MONO_HLSB)
                self.oled.fill(0)
                self.oled.blit(fbuf, 0, 0)
                self.oled.show()
                del fbuf
                time.sleep(0.35)
        else:
            frame_counter = None
            self.re_enter = 0
            self.state = 'Watch'

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
            self.oled.fill(0)
            self.oled.text('fail to update', 0, 31)
            self.oled.show()
            time.sleep(1)
            self.opt_back()

    def manual_update(self):
        # self.real_time_delta = 0
        print('load fonts')
        # 加载字库
        self.fonts = []
        for ff in range(10):
            dirt = '/time_fonts/' + str(ff)
            with open(dirt, 'rb') as f:
                data = bytearray(json.loads(f.read()))
                self.fonts.append(framebuf.FrameBuffer(data, 16, 32, framebuf.MONO_HLSB))
        dirt = '/time_fonts/colon'
        with open(dirt, 'rb') as f:
            data = bytearray(json.loads(f.read()))
            self.fonts.append(framebuf.FrameBuffer(data, 16, 32, framebuf.MONO_HLSB))
        for i in range(6):
            while (True):
                self.oled.fill(0)
                timenow = time.localtime(time.time() + self.real_time_delta)
                self.oled_element = [str(i), 'update',
                                     None, False, None,
                                     False, timenow, timenow, False, None, None]
                self.generator()
                self.oled.show()
                time.sleep(0.1)
                if self.opt_enter_is_pressed:
                    self.opt_enter_is_pressed = 0
                    break
                if self.opt_navi_is_pressed:
                    self.opt_navi_is_pressed = 0
                    if i == 0:
                        self.real_time_delta += 3600
                    elif i == 1:
                        self.real_time_delta += 60
                    elif i == 2:
                        self.real_time_delta += 1
                    elif i == 3:
                        self.real_time_delta += 31536000
                    elif i == 4:
                        self.real_time_delta += 2592000
                    elif i == 5:
                        self.real_time_delta += 86400
        self.state = 'Watch'

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
        if led_notice_flag == 1:
            state_led_pin.value(1 - led_state_flag)
            led_state_flag = 1 - led_state_flag
            time.sleep(0.1)
        if stat == 'idle' or not stat:
            state_led_pin.value(0)
            # led_state_flag=0
        elif stat == 'warning' or stat == 1:
            state_led_pin.value(1)
            # led_state_flag=1
        elif stat == 'message':
            led_notice_flag = 1

    def column(self):
        self.state = 'Column'
        globals()[self.working_menu[self.array].replace(' ', '')] += 1
        if globals()[self.working_menu[self.array].replace(' ', '')] == 6: globals()[
            self.working_menu[self.array].replace(' ', '')] = 0
        self.oled.fill(0)
        self.oled.text(str(globals()[self.working_menu[self.array].replace(' ', '')]), 60, 30, )
        self.oled.contrast(int(oledcontrast * 25.2) + 1)
        self.oled.show()

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