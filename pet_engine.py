
import math
import time
import framebuf
from machine import PWM, Pin, RTC
from weather_ui import WeatherUI

import config
from eye_graphics import draw_centered_eye_pair
from games import SpinMatchGame
from app_features import WeatherApp, AlarmApp, StopwatchApp


class RotaryEncoder:
    """Hardware ISR Rotary Encoder using Gray Code State Table."""

    # Full-step state table for quadrature decoding
    # Returns: 0 (no move), 1 (CW), -1 (CCW)
    STATE_TABLE = (
        0, 1, -1, 0,
        -1, 0, 0, 1,
        1, 0, 0, -1,
        0, -1, 1, 0
    )

    def __init__(self, pin_a, pin_b):
        self.pin_a = pin_a
        self.pin_b = pin_b
        
        # Track 2-bit state (AB)
        self.state = (self.pin_a.value() << 1) | self.pin_b.value()
        self.delta = 0

        # Hardware Interrupts on BOTH edges for maximum resolution
        self.pin_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._irq_handler)
        self.pin_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._irq_handler)

    def _irq_handler(self, pin):
        # Sample current AB values
        curr_ab = (self.pin_a.value() << 1) | self.pin_b.value()
        
        # Calculate index into state table: (old_state << 2) | new_state
        idx = (self.state << 2) | curr_ab
        self.state = curr_ab

        # Update position delta
        movement = self.STATE_TABLE[idx]
        if movement != 0:
            self.delta += movement

    def read(self):
        """Returns step increment (-1, 0, or 1)."""
        if self.delta >= 2:       # Threshold filters micro-bounces
            self.delta -= 2
            return 1
        elif self.delta <= -2:
            self.delta += 2
            return -1
        return 0


class Tamagotchi:
    def __init__(self, display):
        self.display = display
        self.hunger = 80
        self.happiness = 70
        self.energy = 90
        self.steps = 0
        self.battery_pct = 100  # Default 100% capacity

        self.state = "IDLE"
        self.menu_index = 0
        self.menu_items = [
            "Feed",
            "Play",
            "Sleep",
            "Games",
            "Status",
            "Weather",
            "Alarm",
            "Stopwatch",
            "Back",
        ]

        # Sub-modules
        self.wifi_connected = False
        self.time_str = "--:--"
        self.game = SpinMatchGame(display)
        self.weather = WeatherUI(display)
        self.alarm = AlarmApp(display)
        self.stopwatch = StopwatchApp(display)

        # Character State & Animations
        self.char_x = 48.0
        self.slide_dir = 1.0
        self.move_speed = 0.5
        self.deep_idle = False
        self.character_blink = False

        self.is_walking = False
        self.last_step_time = time.ticks_ms()
        self.walk_step_frame = 0
        self.bounce_y = 0

        self.look_dir = 0
        self.talk_text = ""
        self.show_talk = False
        self.last_talk = time.ticks_ms()
        self.last_interaction = time.ticks_ms()
        self.last_blink = time.ticks_ms()

        self.buzzer = PWM(Pin(config.PIN_BUZZER), freq=1000, duty_u16=0)

    def activity_detected(self):
        self.deep_idle = False
        self.last_interaction = time.ticks_ms()

    def register_step(self):
        self.steps += 1
        self.is_walking = True
        self.walk_step_frame += 1
        self.last_step_time = time.ticks_ms()
        self.bounce_y = -4 if (self.walk_step_frame % 2 == 1) else 0
        self.activity_detected()

    def beep(self, freq, dur_ms):
        self.buzzer.freq(freq)
        self.buzzer.duty_u16(32768)
        time.sleep_ms(dur_ms)
        self.buzzer.duty_u16(0)

    def draw_bitmap(self, byte_data, x, y, w=32, h=32):
        fb = framebuf.FrameBuffer(byte_data, w, h, framebuf.MONO_HLSB)
        self.display.blit(fb, int(x), int(y))

    def draw_top_bar(self):
        # Wi-Fi Indicator (Left side)
        if self.wifi_connected:
            self.display.pixel(5, 6, 1)
            self.display.hline(4, 4, 3, 1)
            self.display.hline(3, 2, 5, 1)
        else:
            self.display.text("x", 2, 0)

        # Dynamically read current time from internal RTC (Center)
        try:
            tm = RTC().datetime()
            self.time_str = f"{tm[4]:02d}:{tm[5]:02d}"
        except Exception:
            pass

        self.display.text(self.time_str, 44, 0)

        # Battery Icon (Right side: x=112, y=1)
        # Outer shell (12x6 pixels)
        self.display.rect(112, 1, 12, 6, 1)
        # Positive terminal nub
        self.display.vline(124, 2, 4, 1)
        # Inner fill calculation (max 8 pixels wide)
        fill_width = int((getattr(self, 'battery_pct', 100) / 100) * 8)
        if fill_width > 0:
            self.display.fill_rect(114, 3, fill_width, 2, 1)

    def render_idle(self):
        now = time.ticks_ms()
        if self.is_walking and time.ticks_diff(now, self.last_step_time) > 1500:
            self.is_walking = False
            self.bounce_y = 0

        if time.ticks_diff(now, self.last_interaction) > 10000:
            self.deep_idle = True

        if self.deep_idle:
            draw_centered_eye_pair(
                self.display,
                is_blink=self.character_blink,
                look_dir=self.look_dir,
            )
        else:
            self.display.fill(0)
            self.draw_top_bar()
            bmp = (
                config.FACE_BLINK
                if self.character_blink
                else config.FACE_NORMAL
            )

            if self.is_walking:
                self.char_x = 48.0
                draw_y = 12 + self.bounce_y
            else:
                self.char_x += self.slide_dir * self.move_speed
                if self.char_x >= 96.0:
                    self.char_x = 96.0
                    self.slide_dir = -1.0
                elif self.char_x <= 0.0:
                    self.char_x = 0.0
                    self.slide_dir = 1.0
                draw_y = 12

            self.draw_bitmap(bmp, int(self.char_x), draw_y)

            if self.is_walking:
                self.display.fill_rect(0, 48, 128, 16, 1)
                self.display.text("WALK", 4, 52, 0)
                self.display.text(f"Steps:{self.steps}", 48, 52, 0)
            elif self.show_talk and (
                time.ticks_diff(now, self.last_talk) < 2500
            ):
                self.display.text(self.talk_text, 10, 48)
            else:
                self.show_talk = False
                self.draw_mini_bars()

        self.display.show()

    def draw_mini_bars(self):
        self.display.text("H", 2, 54)
        self.display.rect(12, 56, 26, 5, 1)
        self.display.fill_rect(12, 56, int((self.hunger / 100) * 26), 5, 1)

        self.display.text("P", 48, 54)
        self.display.rect(58, 56, 26, 5, 1)
        self.display.fill_rect(58, 56, int((self.happiness / 100) * 26), 5, 1)

        self.display.text("E", 94, 54)
        self.display.rect(104, 56, 22, 5, 1)
        self.display.fill_rect(104, 56, int((self.energy / 100) * 22), 5, 1)

    def render_menu(self):
        self.display.fill(0)
        self.draw_top_bar()
        self.display.text("MENU", 48, 9)
        self.display.hline(0, 18, 128, 1)

        items_visible = 4
        item_height = 11
        start_y = 21
        scroll_offset = max(
            0,
            min(
                self.menu_index - items_visible + 1,
                len(self.menu_items) - items_visible,
            ),
        )

        for i in range(items_visible):
            idx = scroll_offset + i
            if idx >= len(self.menu_items):
                break
            y = start_y + (i * item_height)
            if idx == self.menu_index:
                self.display.fill_rect(4, y - 1, 120, item_height - 1, 1)
                self.display.text(self.menu_items[idx], 10, y + 1, 0)
            else:
                self.display.text(self.menu_items[idx], 10, y + 1, 1)

        self.display.show()

    def render_status(self):
        self.display.fill(0)
        self.draw_top_bar()
        self.display.text("STATUS", 40, 9)
        self.display.hline(0, 18, 128, 1)
        self.display.text(f"Hunger   : {int(self.hunger)}%", 2, 22)
        self.display.text(f"Happiness: {int(self.happiness)}%", 2, 32)
        self.display.text(f"Energy   : {int(self.energy)}%", 2, 42)
        self.display.text(f"Steps    : {self.steps}", 2, 52)
        self.display.show()

    def render_weather(self):
        self.weather.render()