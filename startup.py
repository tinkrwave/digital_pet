import time
import uasyncio as asyncio


def draw_bold_header(display, text, x, y):
    """Draws large retro header text on Page 1."""
    import framebuf

    char_buf = bytearray(8)
    fb = framebuf.FrameBuffer(char_buf, 8, 8, framebuf.MONO_HMSB)

    for i, char in enumerate(text):
        fb.fill(0)
        fb.text(char, 0, 0, 1)
        char_x = x + (i * 11)
        for row in range(8):
            for col in range(8):
                if fb.pixel(col, row):
                    display.fill_rect(char_x + col, y + (row * 2), 2, 2, 1)


def draw_icon_mpu(display, x, y, ok=True):
    """Draws an 8x8 gyro/accel icon."""
    if ok:
        display.rect(x + 1, y + 1, 6, 6, 1)
        display.pixel(x + 3, y + 3, 1)
    else:
        display.line(x + 1, y + 1, x + 6, y + 6, 1)
        display.line(x + 6, y + 1, x + 1, y + 6, 1)


def draw_icon_wifi(display, x, y, ok=True):
    """Draws an 8x8 Wi-Fi icon."""
    if ok:
        display.pixel(x + 3, y + 6, 1)
        display.line(x + 1, y + 4, x + 5, y + 4, 1)
        display.line(x, y + 2, x + 6, y + 2, 1)
    else:
        display.line(x, y + 6, x + 6, y, 1)


async def run_startup_sequence(
    display, pet, has_mpu, calibrate_mpu_fn, connect_wifi_fn
):
    """Retro command-line boot sequence with fixed line persistence."""
    # -------------------------------------------------------------
    # PAGE 1: Big Title Screen
    # -------------------------------------------------------------
    display.fill(0)

    # Large "tinkrwave" centered vertically
    draw_bold_header(display, "tinkrwave", 14, 14)

    # Subtitle in small font below
    display.text("build.break.learn.", 1, 38, 1)
    display.show()
    pet.beep(1200, 40)

    await asyncio.sleep_ms(1800)

    # -------------------------------------------------------------
    # PAGE 2: Terminal Diagnostic Screen
    # -------------------------------------------------------------
    display.fill(0)
    display.show()

    # --- TOP LINE (y=4): MPU Calibration ---
    display.text("> calib mpu", 2, 4, 1)
    display.show()

    if has_mpu:
        calibrate_mpu_fn()
        # Re-render line text in case calibrate_mpu_fn modified the display
        display.text("> calib mpu", 2, 4, 1)
        draw_icon_mpu(display, 98, 4, ok=True)
        display.text("ok", 112, 4, 1)
        pet.beep(1600, 30)
    else:
        display.text("> calib mpu", 2, 4, 1)
        draw_icon_mpu(display, 98, 4, ok=False)
        display.text("x", 112, 4, 1)
        pet.beep(600, 80)

    display.show()
    await asyncio.sleep_ms(500)

    # --- MIDDLE LINE (y=24): Wi-Fi Connection ---
    display.text("> wifi init", 2, 24, 1)
    display.show()

    connect_wifi_fn(pet)

    # Maintain existing line 1 on screen while rendering line 2
    display.text("> calib mpu", 2, 4, 1)
    if has_mpu:
        draw_icon_mpu(display, 98, 4, ok=True)
        display.text("ok", 112, 4, 1)
    else:
        draw_icon_mpu(display, 98, 4, ok=False)
        display.text("x", 112, 4, 1)

    display.text("> wifi init", 2, 24, 1)
    if pet.wifi_connected:
        draw_icon_wifi(display, 98, 24, ok=True)
        display.text("ok", 112, 24, 1)
        pet.beep(2000, 50)
    else:
        draw_icon_wifi(display, 98, 24, ok=False)
        display.text("x", 112, 24, 1)
        pet.beep(500, 100)

    display.show()
    await asyncio.sleep_ms(600)

    # --- BOTTOM LINE (y=44): System Ready Prompt ---
    display.text("> sys ready", 2, 44, 1)

    for _ in range(3):
        display.fill_rect(90, 44, 6, 8, 1)
        display.show()
        pet.beep(2400, 20)
        await asyncio.sleep_ms(180)

        display.fill_rect(90, 44, 6, 8, 0)
        display.show()
        await asyncio.sleep_ms(180)

    # Boot completion chime
    pet.beep(1400, 50)
    await asyncio.sleep_ms(60)
    pet.beep(1800, 50)
    await asyncio.sleep_ms(60)
    pet.beep(2400, 90)
    await asyncio.sleep_ms(200)