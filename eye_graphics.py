# eye_graphics.py
import time


def draw_retro_eye(
    display, x, y, is_blink=False, look_dir=0, expression="normal", is_right_eye=False
):
    """Draws pixel-art eyes with support for normal capsule eyes, animated loved hearts,

    and a tall frightened eye with smooth curved eyebrows and a round centered pupil.

    :param display: SSD1306/FrameBuffer instance
    :param x: Top-left X position
    :param y: Top-left Y position
    :param is_blink: Render as a horizontal blink line if True
    :param look_dir: Horizontal shift offset (-1 for left, 0 center, 1 right)
    :param expression: Expression overlay ("normal", "loved", "shocked")
    :param is_right_eye: True if rendering the right eye (for mirroring eyebrows)
    """
    x = x + (look_dir * 3)  # Shift eye horizontally based on look direction

    if is_blink:
        # 16x3 pixel sleek blink line
        display.fill_rect(x + 1, y + 13, 16, 3, 0)
        return

    if expression == "shocked":
        # === FRIGHTENED / SHOCKED MODE: Smooth Eyebrows + Black Ellipse + Round White Pupil ===

        # 1. Smooth Curved Eyebrows (2px thick, arched upward toward center)
        if not is_right_eye:
            # Left Eyebrow
            display.fill_rect(x - 3, y - 6, 4, 2, 0)
            display.fill_rect(x + 1, y - 8, 4, 2, 0)
            display.fill_rect(x + 5, y - 10, 5, 2, 0)
            display.fill_rect(x + 10, y - 12, 5, 2, 0)
            display.fill_rect(x + 15, y - 13, 3, 2, 0)
        else:
            # Right Eyebrow (Mirrored)
            display.fill_rect(x, y - 13, 3, 2, 0)
            display.fill_rect(x + 3, y - 12, 5, 2, 0)
            display.fill_rect(x + 8, y - 10, 5, 2, 0)
            display.fill_rect(x + 13, y - 8, 4, 2, 0)
            display.fill_rect(x + 17, y - 6, 4, 2, 0)

        # 2. Outer Black Ellipse (20px wide x 38px high)
        display.fill_rect(x - 1, y + 6, 20, 16, 0)  # Core wide band
        display.fill_rect(x, y + 3, 18, 22, 0)  # Mid expansion
        display.fill_rect(x + 1, y, 16, 28, 0)  # Inner curve expansion
        display.fill_rect(x + 2, y - 2, 14, 32, 0)  # Extended vertical reach
        display.fill_rect(x + 3, y - 4, 12, 36, 0)  # Tapering top/bottom
        display.fill_rect(x + 5, y - 5, 8, 38, 0)  # Curved top & bottom tips

        # 3. Pure Round White Pupil (6x6 Circle at Exact Center)
        display.fill_rect(x + 7, y + 11, 4, 6, 1)  # Vertical core
        display.fill_rect(x + 6, y + 12, 6, 4, 1)  # Horizontal core

    elif expression == "loved":
        # === ROTATED / LOVED MODE: Big Round Eye + Animated Flying Heart ===

        # 1. Big Round Eye Body (20x20 pixel circle)
        display.fill_rect(x - 1, y + 8, 20, 12, 0)
        display.fill_rect(x + 1, y + 6, 16, 16, 0)
        display.fill_rect(x + 3, y + 4, 12, 20, 0)

        # White Catchlight (4x4 block)
        display.fill_rect(x + 10, y + 7, 4, 4, 1)

        # 2. Animated Flying Heart
        float_offset = (time.ticks_ms() // 50) % 12
        hx = x + 4
        hy = (y - 2) - float_offset

        if hy > -8:
            display.fill_rect(hx + 1, hy, 3, 1, 0)
            display.fill_rect(hx + 6, hy, 3, 1, 0)
            display.fill_rect(hx, hy + 1, 10, 2, 0)
            display.fill_rect(hx + 1, hy + 3, 8, 2, 0)
            display.fill_rect(hx + 2, hy + 5, 6, 1, 0)
            display.fill_rect(hx + 3, hy + 6, 4, 1, 0)
            display.fill_rect(hx + 4, hy + 7, 2, 1, 0)

    else:
        # === IDLE / NORMAL MODE: Original Capsule Eye ===

        # 1. Main Black Capsule Body (18px wide x 28px high)
        display.fill_rect(x, y + 5, 18, 18, 0)
        display.fill_rect(x + 1, y + 3, 16, 22, 0)
        display.fill_rect(x + 2, y + 2, 14, 24, 0)
        display.fill_rect(x + 3, y + 1, 12, 26, 0)
        display.fill_rect(x + 4, y, 10, 28, 0)

        # 2. White Catchlight / Highlight Block
        display.fill_rect(x + 10, y + 5, 5, 6, 1)


def draw_centered_eye_pair(
    display, is_blink=False, look_dir=0, expression="normal"
):
    """Renders the eye pair centered on a 128x64 display."""
    display.fill(1)

    # Left eye
    draw_retro_eye(
        display,
        32,
        18,
        is_blink=is_blink,
        look_dir=look_dir,
        expression=expression,
        is_right_eye=False,
    )
    # Right eye
    draw_retro_eye(
        display,
        78,
        18,
        is_blink=is_blink,
        look_dir=look_dir,
        expression=expression,
        is_right_eye=True,
    )