import icrobot
import time
import _thread
import gc
from machine import Pin,reset
import module
import esp_audio
import esp_camera
import esp_who
import ota
timeout = 10  # 设定10秒的超时时间
last_pressed_time = None  # 记录按键按下的时间
power = Pin(6, Pin.IN, Pin.PULL_UP)
file_id = None

def execute_file(filename):
    try:
        with open(filename, 'r') as file:
            code = file.read()
        icrobot.start_execution()
        time.sleep_ms(100)
        exec(code, globals())
    except Exception as e:
        print(e)

def power_callback(pin):
    if power.value() == 0:
        icrobot.mode_flag = True
        icrobot.file_start_flag = not icrobot.file_start_flag
        print(icrobot.file_start_flag)
    if power.value() == 1:
        icrobot.mode_flag = False
        
if __name__ == '__main__':
    gc.enable()
    icrobot.start_receive()
    power.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=power_callback)
    with open("/flash/key.wav", 'rb') as f:
        f.seek(1024)  # 跳过 WAV 文件头部，直接读取音频数据     
        key = f.read()
    with open("/mode.txt", "r") as f:
        mode =  f.read().strip()
    if mode == "ap":
        icrobot.wifi.start_ap()
        host = "192.168.4.1"
        icrobot.video_start(host)
        _thread.start_new_thread(icrobot.scratch.start_receive,(host,),5*1024)
        _thread.start_new_thread(icrobot.scratch.start_send, (host,),3*1024)
        _thread.start_new_thread(icrobot.scratch.start_mode, (host,),4*1024)
        _thread.start_new_thread(icrobot.scratch.start_speaker, (host,),4*1024)
        # _thread.start_new_thread(icrobot.scratch.start_usart_receive,(),5*1024)
        _thread.start_new_thread(icrobot.scratch.start_usart_send, (),3*1024)
        while True:
            gc.collect()
            if icrobot.file_flag:
                if not icrobot.start:
                    if icrobot.leftkey.value() == 0:
                        esp_audio.music_play(key)
                        while icrobot.leftkey.value() == 0:
                            pass
                        icrobot.file_num = icrobot.file_num + 1
                        if icrobot.file_num > 6:
                            icrobot.file_num = 1
                        icrobot.power.set_status(icrobot.file_num)
                        last_pressed_time = time.time()
                    if icrobot.rightkey.value() == 0:
                        esp_audio.music_play(key)
                        while icrobot.rightkey.value() == 0:
                            pass
                        icrobot.file_num = icrobot.file_num - 1
                        if icrobot.file_num < 1:
                            icrobot.file_num = 6
                        icrobot.power.set_status(icrobot.file_num)
                        last_pressed_time = time.time()
                    if last_pressed_time and time.time() - last_pressed_time >= timeout:
                        if not icrobot.file_start_flag:
                            icrobot.file_num = 0
                            icrobot.power.set_status(255)
                        last_pressed_time = None
                if icrobot.file_start_flag and not icrobot.start: 
                    if icrobot.file_num == 0:
                        for count in range(2):
                            icrobot.display.show_image([0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x40,0x40,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0],0)
                            time.sleep(0.2)
                            icrobot.display.show_image([0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x20,0x10,0x50,0x50,0x10,0x20,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0],0)
                            time.sleep(0.2)
                            icrobot.display.show_image([0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x10,0x8,0x24,0x14,0x54,0x54,0x14,0x24,0x8,0x10,0x0,0x0,0x0,0x0,0x0,0x0,0x0],0)
                            time.sleep(0.2)
                        icrobot.file_start_flag = False
                        icrobot.power.set_status(255)
                        continue
                    file_path = icrobot.file_path[icrobot.file_num-1]
                    if icrobot.file_num == 6:
                        time.sleep(0.2)
                        icrobot.start = True
                        execute_file(file_path)
                        icrobot.stop_execution(1)
                        icrobot.start = False
                        icrobot.file_start_flag = False
                    else:
                        file_id = _thread.start_new_thread(execute_file, (file_path,),6*1024)
                        icrobot.start = True
                if not icrobot.file_start_flag and icrobot.start: 
                    icrobot.speaker.music_flag = False
                    icrobot.rgb_sensor.line_flag = False
                    icrobot.ai.ai_start = False
                    icrobot.rgb_sensor.anti_fall_flag = False
                    _thread.delete(file_id)
                    file_id = None
                    last_pressed_time = None  # 记录按键按下的时间
                    if icrobot.scratch.file_end:
                        icrobot.file_flag = False
                    icrobot.scratch.file_end = False
                    icrobot.stop_execution(1)
                    icrobot.wifi.start_ap()
                    icrobot.file_start_flag = False
                    icrobot.start = False
            time.sleep(0.1)
    if mode == "sta":
        # _thread.start_new_thread(icrobot.scratch.start_usart_receive,(),5*1024)
        _thread.start_new_thread(icrobot.scratch.start_usart_send, (),3*1024)
        _thread.start_new_thread(icrobot.wifi.scan_and_connect_wifi, (),3*1024)
        while True:
            gc.collect()
            # if icrobot.wifi.scaned:
            #     if not icrobot.wifi.is_connected():
            #         if not icrobot.wifi.reconnect:
            #             icrobot.file_flag = True
            #             icrobot.stop_execution()
            #             _thread.start_new_thread(icrobot.wifi.reconnect_wifi, (),3*1024)
            #             icrobot.wifi.reconnect = True
            if icrobot.file_flag:
                if not icrobot.start:
                    if icrobot.leftkey.value() == 0:
                        esp_audio.music_play(key)
                        icrobot.wifi.scan_flag = False
                        while icrobot.leftkey.value() == 0:
                            pass
                        icrobot.file_num = icrobot.file_num + 1
                        if icrobot.file_num > 6:
                            icrobot.file_num = 1
                        icrobot.power.set_status(icrobot.file_num)
                        last_pressed_time = time.time()
                    if icrobot.rightkey.value() == 0:
                        icrobot.wifi.scan_flag = False
                        esp_audio.music_play(key)
                        while icrobot.rightkey.value() == 0:
                            pass
                        icrobot.file_num = icrobot.file_num - 1
                        if icrobot.file_num < 1:
                            icrobot.file_num = 6
                        icrobot.power.set_status(icrobot.file_num)
                        last_pressed_time = time.time()
                    if last_pressed_time and time.time() - last_pressed_time >= timeout:
                        # 如果没有进入 `file_start_flag` 判断，就显示另一个表情
                        if not icrobot.file_start_flag:
                            icrobot.file_num = 0
                            icrobot.power.set_status(255)
                            icrobot.wifi.scan_flag = True
                        # 重置 last_pressed_time，防止每次循环都进入超时判断
                        last_pressed_time = None
                if icrobot.file_start_flag and not icrobot.start: 
                    if icrobot.file_num == 0:
                        for count in range(2):
                            icrobot.display.show_image([0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x66,0x42,0x2,0x2,0x42,0x66,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0],0)
                            time.sleep(0.2)
                            icrobot.display.show_image([0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x66,0x46,0x4,0x4,0x46,0x66,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0],0)
                            time.sleep(0.2)
                            icrobot.display.show_image([0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x6E,0x4A,0x8,0x8,0x4A,0x6E,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0],0)
                            time.sleep(0.2)
                            icrobot.display.show_image([0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x76,0x52,0x10,0x10,0x52,0x76,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0],0)
                            time.sleep(0.2)
                            icrobot.display.show_image([0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x66,0x62,0x20,0x20,0x62,0x66,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0],0)
                            time.sleep(0.2)
                            icrobot.display.show_image([0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x66,0x42,0x40,0x40,0x42,0x66,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0],0)
                            time.sleep(0.2)
                        icrobot.file_start_flag = False
                        icrobot.power.set_status(255)
                        continue
                    file_path = icrobot.file_path[icrobot.file_num-1]
                    if icrobot.file_num == 6:
                        time.sleep(0.2)
                        icrobot.start = True
                        execute_file(file_path)
                        icrobot.stop_execution(1)
                        icrobot.start = False
                        icrobot.file_start_flag = False
                    else:
                        file_id = _thread.start_new_thread(execute_file, (file_path,),6*1024)
                        icrobot.start = True

                if not icrobot.file_start_flag and icrobot.start: 
                    icrobot.speaker.music_flag = False
                    icrobot.rgb_sensor.line_flag = False
                    if icrobot.scratch.file_end:
                        icrobot.file_flag = False
                    icrobot.scratch.file_end = False
                    if icrobot.wifi.scaned:
                        icrobot.ai.ai_start = False
                        icrobot.stop_execution(1)
                    else:
                        icrobot.stop_execution(0)
                    icrobot.rgb_sensor.anti_fall_flag = False
                    _thread.delete(file_id)
                    file_id = None
                    last_pressed_time = None  # 记录按键按下的时间
                    icrobot.wifi.scan_flag = True
                    icrobot.file_start_flag = False
                    icrobot.start = False
            time.sleep_ms(100)
    if mode == "bluetooth":
        ble = icrobot.ESP32S3_BLE(str(icrobot.wifi.chip_id[-4:]))
        # _thread.start_new_thread(icrobot.scratch.start_usart_receive,(),5*1024)
        _thread.start_new_thread(icrobot.scratch.start_usart_send, (),2500)
        while True:
            gc.collect()
            if icrobot.file_flag:
                if not icrobot.start:
                    if icrobot.leftkey.value() == 0:
                        esp_audio.music_play(key)
                        while icrobot.leftkey.value() == 0:
                            pass
                        icrobot.file_num = icrobot.file_num + 1
                        if icrobot.file_num > 6:
                            icrobot.file_num = 1
                        icrobot.power.set_status(icrobot.file_num)
                        last_pressed_time = time.time()
                    if icrobot.rightkey.value() == 0:
                        esp_audio.music_play(key)
                        while icrobot.rightkey.value() == 0:
                            pass
                        icrobot.file_num = icrobot.file_num - 1
                        if icrobot.file_num < 1:
                            icrobot.file_num = 6
                        icrobot.power.set_status(icrobot.file_num)
                        last_pressed_time = time.time()
                    if last_pressed_time and time.time() - last_pressed_time >= timeout:
                        # 如果没有进入 `file_start_flag` 判断，就显示另一个表情
                        if not icrobot.file_start_flag:
                            icrobot.file_num = 0
                            icrobot.power.set_status(255)
                        # 重置 last_pressed_time，防止每次循环都进入超时判断
                        last_pressed_time = None
                if icrobot.file_start_flag and not icrobot.start: 
                    if icrobot.file_num == 0:
                        for count in range(2):
                            icrobot.display.show_image([0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x28,0x7C,0x54,0x28,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0],0)
                            time.sleep(0.2)
                            icrobot.display.show_image([0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x44,0x28,0xFF,0x91,0xAA,0x44,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0],0)
                            time.sleep(0.2)
                        icrobot.file_start_flag = False
                        icrobot.power.set_status(255)
                        continue
                    file_path = icrobot.file_path[icrobot.file_num-1]
                    if icrobot.file_num == 6:
                        time.sleep(0.2)
                        icrobot.start = True
                        execute_file(file_path)
                        icrobot.stop_execution(1)
                        icrobot.start = False
                        icrobot.file_start_flag = False
                    else:
                        file_id = _thread.start_new_thread(execute_file, (file_path,),6*1024)
                        icrobot.start = True
                if not icrobot.file_start_flag and icrobot.start: 
                    icrobot.speaker.music_flag = False
                    icrobot.rgb_sensor.line_flag = False
                    icrobot.ai.ai_start = False
                    icrobot.asr.asr_start = False
                    icrobot.rgb_sensor.anti_fall_flag = False
                    _thread.delete(file_id)
                    if icrobot.scratch.file_end:
                        icrobot.file_flag = False
                    icrobot.scratch.file_end = False
                    file_id = None
                    last_pressed_time = None  # 记录按键按下的时间
                    icrobot.stop_execution(1)
                    icrobot.file_start_flag = False
                    icrobot.start = False
            time.sleep(0.2)