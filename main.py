import math
import random
import time
import uasyncio as asyncio


# Safe Hardware Imports
try:
    import urequests
except ImportError:
    urequests = None

from machine import I2C, RTC, Pin
import config
import eye_graphics
import ssd1306
import startup
from pet_engine import RotaryEncoder, Tamagotchi

try:
    import mpu6050

    HAS_MPU = True
except ImportError:
    HAS_MPU = False

try:
    import network
    import ntptime

    HAS_WIFI = True
except ImportError:
    HAS_WIFI = False

# ================== INITIALIZATION ==================
i2c = I2C(0, sda=Pin(config.PIN_SDA), scl=Pin(config.PIN_SCL), freq=400000)
display = ssd1306.SSD1306_I2C(128, 64, i2c)

if HAS_MPU:
    try:
        mpu_sensor = mpu6050.accel(i2c)
    except Exception:
        HAS_MPU = False

pin_a = Pin(config.PIN_ENC_A, Pin.IN, Pin.PULL_UP)
pin_b = Pin(config.PIN_ENC_B, Pin.IN, Pin.PULL_UP)
encoder_sw = Pin(config.PIN_ENC_SW, Pin.IN, Pin.PULL_UP)

encoder = RotaryEncoder(pin_a, pin_b)
pet = Tamagotchi(display)

# Global variables for full-screen alerts
active_warning_msg = None
active_warning_expr = None
warning_active_until = 0
last_warning_trigger_time = 0


# ================== EXPRESSION RESOLVER ==================
def get_pet_expression():
    """Maps Tamagotchi vitals to eye expression overlays."""
    health_val = getattr(pet, "health", 100)

    if health_val < 25:
        return "sad"
    elif pet.energy < 20:
        return "sleepy"
    elif pet.hunger < 30:
        return "angry"
    elif pet.happiness < 30:
        return "sad"
    elif pet.happiness > 70:
        return "happy"

    return "normal"


# ================== CALIBRATION & NETWORK ==================
def calibrate_mpu():
    if not HAS_MPU:
        return
    display.fill(0)

    z_sum = 0
    samples = 25
    for _ in range(samples):
        try:
            acc = mpu_sensor.get_values()
            z_sum += (acc["AcZ"] / 16384.0) * 9.8
        except Exception:
            pass
        time.sleep_ms(20)

    pet.base_z = z_sum / samples if samples > 0 else 9.8


def connect_wifi_and_sync_time(pet_obj=None):
    if pet_obj is None:
        pet_obj = pet

    wlan = network.WLAN(network.STA_IF)

    try:
        if not wlan.active():
            wlan.active(True)
            time.sleep_ms(100)

        try:
            wlan.disconnect()
            time.sleep_ms(100)
        except Exception:
            pass

        if not wlan.isconnected():
            print(f"Connecting to Wi-Fi '{config.WIFI_SSID}'...")
            wlan.connect(config.WIFI_SSID, config.WIFI_PASS)

            timeout = 100
            while not wlan.isconnected() and timeout > 0:
                time.sleep_ms(100)
                timeout -= 1

        if wlan.isconnected():
            print("Wi-Fi Connected! IP:", wlan.ifconfig()[0])
            pet_obj.wifi_connected = True

            ntp_servers = ["pool.ntp.org", "time.google.com", "time.nist.gov"]
            synced = False

            for server in ntp_servers:
                try:
                    ntptime.host = server
                    ntptime.settime()
                    synced = True
                    print(f"NTP raw UTC time synced via {server}")
                    break
                except Exception as e:
                    print(f"NTP attempt via {server} failed:", e)

            if synced:
                offset_sec = getattr(config, "UTC_OFFSET_SEC", 20700)
                local_epoch = time.time() + offset_sec
                tm = time.localtime(local_epoch)

                rtc = RTC()
                rtc.datetime(
                    (tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0)
                )

                print("Local RTC time updated:", time.localtime())
        else:
            print("Wi-Fi connection timed out.")
            pet_obj.wifi_connected = False

    except Exception as e:
        print("Wi-Fi / Time Sync Error:", e)
        pet_obj.wifi_connected = False


async def fetch_weather_task():
    while True:
        if pet.wifi_connected and urequests:
            try:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={config.CITY}&appid={config.WEATHER_API_KEY}&units=metric"
                res = urequests.get(url)
                if res.status_code == 200:
                    data = res.json()
                    pet.weather.temp = str(int(data["main"]["temp"]))
                    pet.weather.desc = data["weather"][0]["main"]
                res.close()
            except Exception:
                pass
        await asyncio.sleep(600)


# ================== INPUT & MENU INTERACTION ==================
async def input_task():
    last_sw_state = 1
    press_start_time = 0
    LONG_PRESS_MS = 800

    while True:
        rot = encoder.read()
        if rot != 0:
            pet.activity_detected()

            if pet.state == "IDLE":
                pet.loved_timer = time.ticks_ms()
                pet.last_talk = time.ticks_ms()
                pet.beep(1500, 20)

            elif pet.state == "MENU":
                pet.menu_index = (pet.menu_index + rot) % len(pet.menu_items)
                pet.beep(1500, 10)
            elif pet.state == "GAME":
                pet.game.handle_encoder(rot)
            elif pet.state == "ALARM":
                pet.alarm.handle_encoder(rot)

        sw_val = encoder_sw.value()

        if sw_val == 0 and last_sw_state == 1:
            press_start_time = time.ticks_ms()

        elif sw_val == 1 and last_sw_state == 0:
            press_duration = time.ticks_diff(
                time.ticks_ms(), press_start_time
            )

            if press_duration >= LONG_PRESS_MS:
                pet.activity_detected()
                pet.beep(800, 150)
                if pet.state in [
                    "STATUS",
                    "WEATHER",
                    "ALARM",
                    "STOPWATCH",
                    "GAME",
                ]:
                    pet.state = "MENU"
                elif pet.state == "MENU":
                    pet.state = "IDLE"

            elif press_duration > 50:
                pet.beep(2000, 30)

                if pet.state == "IDLE":
                    pet.activity_detected()
                    if not pet.deep_idle:
                        pet.state = "MENU"
                        pet.menu_index = 0

                elif pet.state == "MENU":
                    pet.activity_detected()
                    selected = pet.menu_items[pet.menu_index]
                    if selected == "Feed":
                        pet.hunger = min(100, pet.hunger + 30)
                        pet.talk_text = "Yum! Yummy!"
                        pet.show_talk = True
                        pet.last_talk = time.ticks_ms()
                        pet.state = "IDLE"
                    elif selected == "Play":
                        pet.happiness = min(100, pet.happiness + 20)
                        pet.talk_text = "Yay! Fun!"
                        pet.show_talk = True
                        pet.last_talk = time.ticks_ms()
                        pet.state = "IDLE"
                    elif selected == "Sleep":
                        pet.energy = min(100, pet.energy + 35)
                        pet.talk_text = "Zzz..."
                        pet.show_talk = True
                        pet.last_talk = time.ticks_ms()
                        pet.state = "IDLE"
                    elif selected == "Games":
                        pet.state = "GAME"
                        pet.game.start()
                    elif selected == "Status":
                        pet.state = "STATUS"
                    elif selected == "Weather":
                        pet.state = "WEATHER"
                    elif selected == "Alarm":
                        pet.state = "ALARM"
                    elif selected == "Stopwatch":
                        pet.state = "STOPWATCH"
                    elif selected == "Back":
                        pet.state = "IDLE"

                elif pet.state == "GAME":
                    pet.activity_detected()
                    if pet.game.is_active:
                        success, reward = pet.game.check_result()
                        if success:
                            pet.happiness = min(100, pet.happiness + reward)
                            pet.beep(1800, 100)
                        else:
                            pet.beep(400, 200)
                    else:
                        pet.state = "MENU"

                elif pet.state == "STOPWATCH":
                    pet.activity_detected()
                    pet.stopwatch.toggle()

                elif pet.state == "ALARM":
                    pet.activity_detected()
                    pet.alarm.toggle()

        last_sw_state = sw_val
        await asyncio.sleep_ms(10)


# ================== ACCELEROMETER / LIFT DETECTION ==================
async def mpu_task():
    if not HAS_MPU:
        return

    gravity = 9.80665
    alpha = 0.85

    sample_buffer = [0.0] * 15
    sample_idx = 0

    last_step_time = 0
    step_candidate_count = 0
    peak_detected = False
    last_shake_time = 0

    MIN_STEP_INTERVAL = 260
    MAX_STEP_INTERVAL = 950
    MIN_AMPLITUDE = 1.8

    while True:
        try:
            acc = mpu_sensor.get_values()

            ax = (acc["AcX"] / 16384.0) * 9.80665
            ay = (acc["AcY"] / 16384.0) * 9.80665
            az = (acc["AcZ"] / 16384.0) * 9.80665

            raw_mag = math.sqrt(ax * ax + ay * ay + az * az)
            gravity = (alpha * gravity) + ((1.0 - alpha) * raw_mag)
            dynamic_accel = abs(raw_mag - gravity)

            now = time.ticks_ms()

            if raw_mag > 25.0 or dynamic_accel > 15.0:
                if time.ticks_diff(now, last_shake_time) > 500:
                    pet.energy = max(0, pet.energy - 15)
                    pet.happiness = max(0, pet.happiness - 5)
                    last_shake_time = now

                pet.shocked_timer = now
                pet.last_talk = now
                pet.activity_detected()

            sample_buffer[sample_idx] = dynamic_accel
            sample_idx = (sample_idx + 1) % 15

            max_val = max(sample_buffer)
            min_val = min(sample_buffer)
            dynamic_threshold = (max_val + min_val) / 2.0
            amplitude = max_val - min_val

            time_since_last = time.ticks_diff(now, last_step_time)

            if dynamic_accel > dynamic_threshold and amplitude > MIN_AMPLITUDE:
                if not peak_detected:
                    peak_detected = True

                    if (
                        MIN_STEP_INTERVAL
                        < time_since_last
                        < MAX_STEP_INTERVAL
                    ):
                        step_candidate_count += 1
                        last_step_time = now

                        if step_candidate_count >= 2:
                            pet.register_step()

                    elif time_since_last >= MAX_STEP_INTERVAL:
                        step_candidate_count = 1
                        last_step_time = now

            elif dynamic_accel < dynamic_threshold:
                peak_detected = False

            if 7.5 < dynamic_accel <= 15.0 and pet.state == "IDLE":
                pet.happiness = min(100, pet.happiness + 2)
                pet.beep(1200, 40)
                pet.activity_detected()

        except Exception:
            pass

        await asyncio.sleep_ms(20)


# ================== STAT DECAY & REMINDERS ==================
async def stat_decay_task():
    global active_warning_msg, active_warning_expr, warning_active_until, last_warning_trigger_time

    while True:
        await asyncio.sleep(1)
        now = time.ticks_ms()

        if getattr(pet, "_last_decay", 0) == 0 or time.ticks_diff(now, pet._last_decay) >= 40000:
            pet.hunger = max(0, pet.hunger - 2)
            pet.happiness = max(0, pet.happiness - 1)
            pet.energy = max(0, pet.energy - 1)
            pet._last_decay = now

        health_val = getattr(pet, "health", 100)

        if time.ticks_diff(now, last_warning_trigger_time) >= 5000:
            if health_val < 25:
                active_warning_msg = "I'm sick! Help!"
                active_warning_expr = "sad"
                pet.beep(500, 300)
            elif pet.hunger < 25:
                active_warning_msg = "Feed me please!"
                active_warning_expr = "angry"
                pet.beep(1000, 150)
            elif pet.energy < 20:
                active_warning_msg = "So sleepy... Zzz"
                active_warning_expr = "sleepy"
                pet.beep(800, 150)
            elif pet.happiness < 25:
                active_warning_msg = "Play with me!"
                active_warning_expr = "sad"
                pet.beep(1200, 100)
            else:
                active_warning_msg = None

            if active_warning_msg:
                warning_active_until = time.ticks_add(now, 2000)
                last_warning_trigger_time = now


# ================== DISPLAY RENDER LOOP ==================
async def render_task():
    last_look_change = time.ticks_ms()
    pet.look_dir = 0

    while True:
        now = time.ticks_ms()

        display.fill(0)

        # --- FULL SCREEN WARNING OVERRIDE (Applies in ANY state) ---
        if active_warning_msg and time.ticks_diff(warning_active_until, now) > 0:
            eye_graphics.draw_centered_eye_pair(
                display,
                is_blink=False,
                look_dir=0,
                expression=active_warning_expr,
            )

            text_x = max(0, (128 - len(active_warning_msg) * 8) // 2)
            display.fill_rect(0, 48, 128, 16, 0)
            display.text(active_warning_msg, text_x, 52, 1)
            display.show()
            await asyncio.sleep_ms(50)
            continue

        is_shocked = (
            time.ticks_diff(now, getattr(pet, "shocked_timer", 0)) < 2000
        )
        is_loved = time.ticks_diff(now, getattr(pet, "loved_timer", 0)) < 2000

        # Random Look Shift
        if time.ticks_diff(now, last_look_change) > 3500:
            pet.look_dir = random.choice([-1, 0, 0, 1])
            last_look_change = now

        # Periodic Blink
        if (
            not pet.character_blink
            and time.ticks_diff(now, pet.last_blink) > 2600
        ):
            pet.character_blink = True
            pet.last_blink = now

        if pet.character_blink and time.ticks_diff(now, pet.last_blink) > 150:
            pet.character_blink = False

        # --- DISPLAY RENDERING STATE MACHINE ---
        if pet.state == "IDLE":
            if is_shocked:
                eye_graphics.draw_centered_eye_pair(
                    display,
                    is_blink=pet.character_blink,
                    look_dir=0,
                    expression="shocked",
                )
                display.show()

            elif is_loved:
                eye_graphics.draw_centered_eye_pair(
                    display,
                    is_blink=pet.character_blink,
                    look_dir=pet.look_dir,
                    expression="loved",
                )
                display.show()

            elif getattr(pet, "deep_idle", False):
                eye_graphics.draw_centered_eye_pair(
                    display,
                    is_blink=pet.character_blink,
                    look_dir=pet.look_dir,
                    expression="normal",
                )
                display.show()

            else:
                expr = get_pet_expression()
                # pet_engine.py handles drawing eye graphics AND talk_text inside render_idle()
                try:
                    pet.render_idle(expression=expr)
                except TypeError:
                    pet.render_idle()

        elif pet.state == "MENU":
            pet.render_menu()
        elif pet.state == "STATUS":
            pet.render_status()
        elif pet.state == "WEATHER":
            pet.weather.render(pet.draw_top_bar)
        elif pet.state == "ALARM":
            pet.alarm.render(pet.draw_top_bar)
        elif pet.state == "STOPWATCH":
            pet.stopwatch.render(pet.draw_top_bar)
        elif pet.state == "GAME":
            pet.game.render()

        await asyncio.sleep_ms(50)


# ================== MAIN STARTUP ==================
async def main():
    await startup.run_startup_sequence(
        display,
        pet,
        HAS_MPU,
        calibrate_mpu,
        connect_wifi_and_sync_time,
    )

    asyncio.create_task(input_task())
    asyncio.create_task(mpu_task())
    asyncio.create_task(stat_decay_task())
    asyncio.create_task(fetch_weather_task())
    await render_task()


asyncio.run(main())