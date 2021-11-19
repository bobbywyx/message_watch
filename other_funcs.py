other_funcs = ('func1', 'func2')


# example:
# 函数需要一个watch参数，此watch就是手表这个对象，这样可以直接访问watch所有类函数和变量，方便外部调用和开发
def func1(watch):
    print('others')
    watch.oled.fill(0)
    watch.oled.text('func1 form out working', 0, 31)
    watch.oled.show()
    watch.time.sleep(2)
    watch.oled.fill(0)
    watch.state = 'Watch'
