import time

class SpinMatchGame:
    def __init__(self, display):
        self.display = display
        self.target = 10
        self.current = 0
        self.start_time = 0
        self.duration = 6  # 6 seconds to match
        self.is_active = False
        self.result_msg = ""
        self.show_result = False

    def start(self):
        import random
        self.target = random.randint(1, 15)
        self.current = 0
        self.start_time = time.ticks_ms()
        self.is_active = True
        self.show_result = False

    def handle_encoder(self, rot):
        """Update selected number via rotary encoder."""
        if self.is_active:
            self.current = max(0, min(20, self.current + rot))

    def check_result(self):
        """Called when button is pressed to submit answer."""
        self.is_active = False
        self.show_result = True
        if self.current == self.target:
            self.result_msg = "WIN! +20 Happy"
            return True, 20  # (success, happiness_reward)
        else:
            self.result_msg = f"MISSED! (Was {self.target})"
            return False, 0

    def render(self):
        self.display.fill(0)
        self.display.text("SPIN MATCH", 24, 4)
        self.display.hline(0, 14, 128, 1)

        if self.is_active:
            elapsed = time.ticks_diff(time.ticks_ms(), self.start_time) // 1000
            remaining = max(0, self.duration - elapsed)

            self.display.text(f"Target: {self.target}", 28, 22)
            self.display.text(f"You   : {self.current}", 28, 36)
            self.display.text(f"Time  : {remaining}s", 36, 52)

            # Auto-fail on timeout
            if remaining == 0:
                self.is_active = False
                self.show_result = True
                self.result_msg = "TIME OUT!"

        elif self.show_result:
            self.display.text(self.result_msg, 8, 32)
            self.display.text("Click to Exit", 12, 50)

        self.display.show()