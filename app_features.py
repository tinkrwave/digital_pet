import time
import config

class WeatherApp:
    def __init__(self, display):
        self.display = display
        self.temp = "--"
        self.desc = "No Data"

    def render(self, draw_top_bar_fn):
        self.display.fill(0)
        draw_top_bar_fn()
        self.display.text("WEATHER", 36, 9)
        self.display.hline(0, 18, 128, 1)
        self.display.text(f"City: {config.CITY}", 4, 24)
        self.display.text(f"Temp: {self.temp} C", 4, 38)
        self.display.text(f"Sky : {self.desc[:12]}", 4, 52)
        self.display.show()


class AlarmApp:
    def __init__(self, display):
        self.display = display
        self.hour = 7
        self.min = 0
        self.enabled = False

    def handle_encoder(self, rot):
        """Adjust alarm time by 5-minute increments."""
        self.min = (self.min + (rot * 5)) % 60

    def toggle(self):
        self.enabled = not self.enabled

    def render(self, draw_top_bar_fn):
        self.display.fill(0)
        draw_top_bar_fn()
        self.display.text("ALARM", 44, 9)
        self.display.hline(0, 18, 128, 1)
        time_str = "{:02d}:{:02d}".format(self.hour, self.min)
        self.display.text(f"Time: {time_str}", 20, 28)
        status = "ENABLED" if self.enabled else "DISABLED"
        self.display.text(f"State: {status}", 8, 44)
        self.display.show()


class StopwatchApp:
    def __init__(self, display):
        self.display = display
        self.running = False
        self.start_time = 0
        self.elapsed = 0

    def toggle(self):
        if not self.running:
            self.running = True
            self.start_time = time.ticks_ms()
        else:
            self.running = False
            self.elapsed += time.ticks_diff(time.ticks_ms(), self.start_time)

    def render(self, draw_top_bar_fn):
        self.display.fill(0)
        draw_top_bar_fn()
        self.display.text("STOPWATCH", 28, 9)
        self.display.hline(0, 18, 128, 1)

        total_elapsed = self.elapsed
        if self.running:
            total_elapsed += time.ticks_diff(time.ticks_ms(), self.start_time)

        secs = (total_elapsed // 1000) % 60
        mins = (total_elapsed // 60000) % 60
        ms = (total_elapsed % 1000) // 10
        sw_str = "{:02d}:{:02d}.{:02d}".format(mins, secs, ms)

        self.display.text(sw_str, 24, 32)
        self.display.text("Click: Start/Stop", 0, 52)
        self.display.show()