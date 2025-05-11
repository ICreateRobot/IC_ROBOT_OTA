# 测试
import time
from machine import Pin

lkey = Pin(5, Pin.IN, Pin.PULL_UP)
rkey = Pin(7, Pin.IN, Pin.PULL_UP)

while rkey.value() == 1:
    time.sleep(0.01)
 
#boot.py
import ota
ota.run()  # 调用 run 函数
