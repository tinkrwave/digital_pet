
import framebuf
import math
import time

try:
    import urequests
except ImportError:
    urequests = None
# ================== 16x16 WEATHER ICON BITMAPS ==================
ICON_SUN = bytearray(
    [
        0x01,
        0x80,
        0x41,
        0x82,
        0x20,
        0x04,
        0x07,
        0xE0,
        0x0F,
        0xF0,
        0x1F,
        0xF8,
        0x1F,
        0xF8,
        0x1F,
        0xF8,
        0x1F,
        0xF8,
        0x0F,
        0xF0,
        0x07,
        0xE0,
        0x20,
        0x04,
        0x41,
        0x82,
        0x01,
        0x80,
        0x00,
        0x00,
        0x00,
        0x00,
    ]
)

ICON_CLOUD = bytearray(
    [
        0x00,
        0x00,
        0x03,
        0xC0,
        0x0C,
        0x30,
        0x10,
        0x08,
        0x21,
        0x84,
        0x46,
        0x42,
        0x48,
        0x22,
        0x90,
        0x11,
        0x90,
        0x09,
        0x60,
        0x06,
        0x00,
        0x00,
        0x7F,
        0xFE,
        0xFF,
        0xFF,
        0x7F,
        0xFE,
        0x00,
        0x00,
        0x00,
        0x00,
    ]
)

ICON_RAIN = bytearray(
    [
        0x03,
        0xC0,
        0x0C,
        0x30,
        0x10,
        0x08,
        0x21,
        0x84,
        0x46,
        0x42,
        0x48,
        0x22,
        0x7F,
        0xFE,
        0x00,
        0x00,
        0x10,
        0x20,
        0x20,
        0x40,
        0x08,
        0x10,
        0x10,
        0x20,
        0x20,
        0x40,
        0x08,
        0x10,
        0x00,
        0x00,
        0x00,
        0x00,
    ]
)

ICON_THUNDER = bytearray(
    [
        0x03,
        0xC0,
        0x0C,
        0x30,
        0x10,
        0x08,
        0x21,
        0x84,
        0x7F,
        0xFE,
        0x00,
        0x00,
        0x03,
        0x00,
        0x06,
        0x00,
        0x0C,
        0x00,
        0x1F,
        0x80,
        0x03,
        0x00,
        0x06,
        0x00,
        0x0C,
        0x00,
        0x08,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
    ]
)

ICON_SNOW = bytearray(
    [
        0x01,
        0x80,
        0x11,
        0x88,
        0x09,
        0x90,
        0x05,
        0xA0,
        0x3F,
        0xFC,
        0x05,
        0xA0,
        0x09,
        0x90,
        0x11,
        0x88,
        0x01,
        0x80,
        0x00,
        0x00,
        0x0A,
        0x50,
        0x04,
        0x20,
        0x0A,
        0x50,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
    ]
)


class WeatherUI:

    def __init__(self, display):
        self.display = display
        self.temp = "--"
        self.desc = "Offline"
        self.city = "Local"

    def fetch_data(self, wifi_connected, config):
        """Fetches weather data from OpenWeatherMap API."""
        if not wifi_connected or not urequests:
            return False

        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={config.CITY}&appid={config.WEATHER_API_KEY}&units=metric"
            res = urequests.get(url)
            if res.status_code == 200:
                data = res.json()
                self.temp = str(int(data["main"]["temp"]))
                self.desc = data["weather"][0]["main"]
                self.city = getattr(config, "CITY", "Local")
            res.close()
            return True
        except Exception as e:
            print("Weather fetch error:", e)
            return False

    def _get_icon_buffer(self, condition):
        cond = condition.lower()
        if (
            "rain" in cond
            or "drizzle" in cond
            or "shower" in cond
            or "thunder" in cond
        ):
            buf = (
                ICON_THUNDER
                if "thunder" in cond or "storm" in cond
                else ICON_RAIN
            )
        elif "snow" in cond or "ice" in cond or "sleet" in cond:
            buf = ICON_SNOW
        elif "cloud" in cond or "overcast" in cond or "mist" in cond:
            buf = ICON_CLOUD
        else:
            buf = ICON_SUN

        return framebuf.FrameBuffer(buf, 16, 16, framebuf.MONO_HLSB)

    def _draw_animations(self, x, y, condition):
        """Dynamic particle animation around weather icon."""
        cond = condition.lower()
        now = time.ticks_ms()

        # Rain animation (falling diagonal drops)
        if "rain" in cond or "drizzle" in cond:
            offset = (now // 80) % 12
            for i in range(3):
                px = x + (i * 12) + (offset // 3)
                py = y + 16 + ((offset + (i * 4)) % 12)
                if py < 62 and px < 124:
                    self.display.line(px, py, px - 1, py + 2, 1)

        # Snow animation (floating particles)
        elif "snow" in cond:
            offset = (now // 150) % 8
            for i in range(4):
                px = x + (i * 10) + int(math.sin((now / 200) + i) * 2)
                py = y + 16 + ((offset + (i * 3)) % 10)
                if py < 62 and px < 124:
                    self.display.pixel(px, py, 1)

        # Clear / Sun pulse effect
        elif "sun" in cond or "clear" in cond:
            pulse = (now // 300) % 2
            if pulse:
                self.display.pixel(x - 2, y + 8, 1)
                self.display.pixel(x + 17, y + 8, 1)
                self.display.pixel(x + 8, y - 2, 1)
                self.display.pixel(x + 8, y + 17, 1)

    def render(self, draw_top_bar_fn=None):
        """Renders stylized weather view."""
        self.display.fill(0)

        # Header / Top Bar
        if draw_top_bar_fn:
            draw_top_bar_fn()
        else:
            self.display.text("WEATHER", 36, 0, 1)
            self.display.hline(0, 10, 128, 1)

        # --- LEFT PANEL: ICON & ANIMATION ---
        icon_fb = self._get_icon_buffer(self.desc)
        icon_x = 12
        icon_y = 20

        self.display.blit(icon_fb, icon_x, icon_y)
        self._draw_animations(icon_x, icon_y, self.desc)

        # Vertical Divider
        self.display.vline(46, 14, 46, 1)

        # --- RIGHT PANEL: DETAILS ---
        # Temperature
        temp_str = f"{self.temp}C"
        self.display.text(temp_str, 54, 18, 1)

        # Condition
        desc_str = self.desc[:9].upper()
        self.display.text(desc_str, 54, 32, 1)

        # Inverted City Badge
        city_str = self.city[:9].upper()
        self.display.fill_rect(52, 46, 72, 13, 1)
        self.display.text(city_str, 56, 49, 0)

        self.display.show()