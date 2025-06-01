import icrobot
import time
import _thread
import gc
from machine import Pin,reset,Timer
import module
import esp_audio
import esp_camera
import esp_who
import esp32ota
timeout = 10  # 设定10秒的超时时间
last_pressed_time = None  # 记录按键按下的时间
power = Pin(6, Pin.IN, Pin.PULL_UP)
file_id = None
low_power_flag = False

def battery_check(timer):
    global low_power_flag
    try:
        if icrobot.uart_receive.power == 1 and icrobot.uart_receive.is_charging == 0:
            low_power_flag = True
    except Exception as e:
        print("电量检测异常:", e)

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
    if power.value() == 1:
        icrobot.mode_flag = False
        
if __name__ == '__main__':
    gc.enable()
    icrobot.start_receive()
    power.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=power_callback)
    with open("/set.txt", "r") as f:
        mode =  f.read().strip()
    _thread.start_new_thread(icrobot.scratch.start_usart_send, (),3*1024)
    icrobot.uart.write(bytearray([0xfe,0xfe,0xfe,0xfe]))
    icrobot.speaker.play_music_until_done("/flash/startup.wav")
    battery_timer = Timer(-1)  # 软件定时器
    battery_timer.init(period=60000, mode=Timer.PERIODIC, callback=battery_check)
    if mode == "ap":
        icrobot.speaker.play_music("/flash/wifi_dis.wav")
        icrobot.wifi.start_ap()
        host = "192.168.4.1"
        icrobot.video_start(host)
        _thread.start_new_thread(icrobot.scratch.start_receive,(host,),5*1024)
        _thread.start_new_thread(icrobot.scratch.start_send, (host,),3*1024)
        _thread.start_new_thread(icrobot.scratch.start_mode, (host,),4*1024)
        _thread.start_new_thread(icrobot.scratch.start_speaker, (host,),4*1024)
        # _thread.start_new_thread(icrobot.scratch.start_usart_receive,(),5*1024)
        while True:
            gc.collect()
            if low_power_flag:
                icrobot.speaker.play_music_until_done("/flash/battery_low.wav")
                low_power_flag = False
            if icrobot.file_flag:
                if not icrobot.start:
                    if icrobot.leftkey.value() == 0:
                        while icrobot.leftkey.value() == 0:
                            pass
                        icrobot.file_num = icrobot.file_num + 1
                        if icrobot.file_num > 6:
                            icrobot.file_num = 1
                        icrobot.display.show_expression((icrobot.file_num-1)|0xd0)
                        last_pressed_time = time.time()
                    if icrobot.rightkey.value() == 0:
                        while icrobot.rightkey.value() == 0:
                            pass
                        icrobot.file_num = icrobot.file_num - 1
                        if icrobot.file_num < 1:
                            icrobot.file_num = 6
                        icrobot.display.show_expression((icrobot.file_num-1)|0xd0)
                        last_pressed_time = time.time()
                    if last_pressed_time and time.time() - last_pressed_time >= timeout:
                        if not icrobot.file_start_flag:
                            icrobot.file_num = 0
                            icrobot.power.set_status(255)
                        last_pressed_time = None
                if icrobot.file_start_flag and not icrobot.start: 
                    if icrobot.file_num == 0:
                        icrobot.display.show_expression(0xc0)
                        icrobot.speaker.play_music_until_done("/flash/mod_ap.wav")
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
        if not icrobot.uart_receive.privacy_switch:
            icrobot.speaker.play_music_until_done("/flash/yinsi_jian.wav")
        while not icrobot.uart_receive.privacy_switch:
            pass
        _thread.start_new_thread(icrobot.wifi.scan_and_connect_wifi, (),3*1024)
        _thread.start_new_thread(icrobot.wifi.reconnect_wifi, (),3*1024)
        while True:
            gc.collect()
            if low_power_flag:
                icrobot.speaker.play_music_until_done("/flash/battery_low.wav")
                low_power_flag = False            
            if icrobot.file_flag:
                if not icrobot.start:
                    if icrobot.leftkey.value() == 0:
                        while icrobot.leftkey.value() == 0:
                            pass
                        icrobot.file_num = icrobot.file_num + 1
                        if icrobot.file_num > 6:
                            icrobot.file_num = 1
                        icrobot.display.show_expression((icrobot.file_num-1)|0xd0)
                        last_pressed_time = time.time()
                    if icrobot.rightkey.value() == 0:
                        while icrobot.rightkey.value() == 0:
                            pass
                        icrobot.file_num = icrobot.file_num - 1
                        if icrobot.file_num < 1:
                            icrobot.file_num = 6
                        icrobot.display.show_expression((icrobot.file_num-1)|0xd0)
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
                        icrobot.display.show_expression(0xc1)
                        icrobot.speaker.play_music_until_done("/flash/mod_sta.wav")
                        icrobot.file_start_flag = False
                        icrobot.power.set_status(255)
                        continue
                    file_path = icrobot.file_path[icrobot.file_num-1]
                    if icrobot.file_num == 6:
                        icrobot.wifi.scan_flag = False
                        time.sleep(0.2)
                        icrobot.start = True
                        execute_file(file_path)
                        if icrobot.wifi.scaned:
                            icrobot.ai.ai_start = False
                            icrobot.stop_execution(1)
                        else:
                            icrobot.stop_execution(0)
                        icrobot.start = False
                        icrobot.file_start_flag = False
                        icrobot.wifi.scan_flag = True
                    else:
                        icrobot.wifi.scan_flag = False
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
        while True:
            gc.collect()
            if low_power_flag:
                icrobot.speaker.play_music_until_done("/flash/battery_low.wav")
                low_power_flag = False            
            if icrobot.file_flag:
                if not icrobot.start:
                    if icrobot.leftkey.value() == 0:
                        while icrobot.leftkey.value() == 0:
                            pass
                        icrobot.file_num = icrobot.file_num + 1
                        if icrobot.file_num > 6:
                            icrobot.file_num = 1
                        icrobot.display.show_expression((icrobot.file_num-1)|0xd0)
                        last_pressed_time = time.time()
                    if icrobot.rightkey.value() == 0:
                        while icrobot.rightkey.value() == 0:
                            pass
                        icrobot.file_num = icrobot.file_num - 1
                        if icrobot.file_num < 1:
                            icrobot.file_num = 6
                        icrobot.display.show_expression((icrobot.file_num-1)|0xd0)
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
                        icrobot.display.show_expression(0xc2)
                        icrobot.speaker.play_music_until_done("/flash/mod_ble.wav")
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
