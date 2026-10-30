"""Halloween minifridge robot, CPX, revision C.

User-approved change: two parallel scene RGB LEDs supply interruption red; no separate red LEDs.
Audio: drinking.wav loops; record_scratch.wav plays once, then radio_static.wav loops.
All three WAV files belong in /audio/ on CIRCUITPY.
No tones or synthesized-audio fallback. See README for setup and power checks.
"""
import time
import math
import random
import board
import digitalio
import pwmio
import audioio
import audiocore
import neopixel

DEBOUNCE_S = 0.035
FRAME_S = 0.04                    # 25 Hz eye updates / pixel output
PIXEL_FLASH_S = 0.20             # new random pixel colors five times per second
SERVO_STEP_S = 0.02
DRINK_ANGLE = 40.0
VIEWER_ANGLE = 110.0              # approximately 70 degrees from drinking pose
SERVO_MIN_US = 1000              # conservative range; calibrate with horn unloaded
SERVO_MAX_US = 2000
PIXEL_CHANNEL_CAP = 12           # raw 0..255 codes; never increase without budgeting


def output(pin, initial):
    io = digitalio.DigitalInOut(pin)
    io.switch_to_output(value=initial)
    return io


# A0's internal amplifier is muted; the external PID 3885 remains powered.
# Do not import adafruit_circuitplayground: it claims peripherals used here.
speaker_enable = output(board.SPEAKER_ENABLE, False)
status_led = output(board.LED, False)
scene_red = output(board.A3, True)     # common-anode outputs: HIGH is OFF
scene_green = output(board.A4, True)
scene_blue = output(board.A5, True)
door = digitalio.DigitalInOut(board.A7)
door.switch_to_input(pull=digitalio.Pull.UP)

# Distinct timers: A1/PA05 TCC0.1, A2/PA06 TCC1.0, A6/PB09 TC4.1.
# A3 is digital; A4/A5 have no usable hardware PWM in this CPX configuration.
eye_red = pwmio.PWMOut(board.A1, frequency=1000, duty_cycle=0)
eye_blue = pwmio.PWMOut(board.A2, frequency=1000, duty_cycle=0)
servo_pwm = pwmio.PWMOut(board.A6, frequency=50, duty_cycle=0)
pixels = neopixel.NeoPixel(board.NEOPIXEL, 10, brightness=1.0, auto_write=False)
pixels.fill((0, 0, 0))
pixels.show()


def set_angle(angle):
    angle = max(0.0, min(180.0, angle))
    pulse = SERVO_MIN_US + (SERVO_MAX_US - SERVO_MIN_US) * angle / 180.0
    servo_pwm.duty_cycle = int(pulse * servo_pwm.frequency * 65535 / 1000000)


def scene(r, g, b):
    scene_red.value = not r
    scene_green.value = not g
    scene_blue.value = not b


audio = audioio.AudioOut(board.A0)
recordings = []                   # references keep stream handles alive
try:
    for filename in ('/audio/drinking.wav', '/audio/record_scratch.wav',
                     '/audio/radio_static.wav'):
        handle = open(filename, 'rb')
        try:
            wav = audiocore.WaveFile(handle)
        except Exception:
            handle.close()
            raise
        recordings.append((handle, wav))
        wav = recordings[-1][1]
        if (wav.channel_count != 1 or wav.sample_rate != 16000
                or wav.bits_per_sample != 16):
            raise ValueError('Need mono 16000Hz signed 16-bit PCM WAV: ' + filename)
except Exception:
    # A missing/invalid recording is a visible setup failure, never a tone fallback.
    audio.stop()
    servo_pwm.duty_cycle = 0
    eye_red.duty_cycle = 0
    eye_blue.duty_cycle = 0
    scene(False, False, False)
    pixels.fill((0, 0, 0))
    pixels.show()
    for handle, wav in recordings:
        wav.deinit()
        handle.close()
    raise

# Contact closed means door shut. At boot, hold the interrupted state until
# the initial switch reading has been stable for the full debounce interval.
now = time.monotonic()
raw_open = bool(door.value)
raw_changed_at = now
interrupted = True
initialized = False
scratch_pending = False
current_angle = VIEWER_ANGLE
target_angle = VIEWER_ANGLE
set_angle(current_angle)
next_frame = now
next_pixel_flash = now
next_servo = now
mode_started = now
palette = ((1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0),
           (0, 1, 1), (1, 0, 1), (1, 1, 1))

try:
    while True:
        now = time.monotonic()
        reading = bool(door.value)
        if reading != raw_open:
            raw_open = reading
            raw_changed_at = now
        if now - raw_changed_at >= DEBOUNCE_S:
            if not initialized or interrupted != raw_open:
                interrupted = raw_open
                initialized = True
                mode_started = now
                target_angle = VIEWER_ANGLE if interrupted else DRINK_ANGLE
                audio.stop()         # stop current file immediately on a mode change
                scratch_pending = interrupted
                if interrupted:
                    audio.play(recordings[1][1], loop=False)
                else:
                    audio.play(recordings[0][1], loop=True)
                # Apply external response immediately, independently of frame timer.
                if interrupted:
                    eye_red.duty_cycle = 65535
                    eye_blue.duty_cycle = 0
                    scene(True, False, False)
                next_frame = now
                next_pixel_flash = now

        # Start static at scratch completion without a programmed pause. Door
        # transitions run first, so closing during scratch cancels this handoff.
        if initialized and interrupted and scratch_pending and not audio.playing:
            scratch_pending = False
            audio.play(recordings[2][1], loop=True)

        # Hardware PWM holds the last servo position between these small steps.
        if now >= next_servo:
            next_servo = now + SERVO_STEP_S
            delta = target_angle - current_angle
            current_angle += max(-2.0, min(2.0, delta))
            set_angle(current_angle)

        if initialized and now >= next_frame:
            next_frame = now + FRAME_S
            elapsed = now - mode_started
            if interrupted:
                eye_red.duty_cycle = 65535
                eye_blue.duty_cycle = 0
                scene(True, False, False)
                # All ten onboard pixels stay solid red while the door is open.
                pixels.fill((PIXEL_CHANNEL_CAP, 0, 0))
            else:
                fade = (math.sin(elapsed * math.pi / 2.0) + 1.0) / 2.0
                eye_red.duty_cycle = int(fade * 65535)
                eye_blue.duty_cycle = 65535
                # Digital combinations retain independent R/G/B control without
                # software PWM that could jitter during streaming WAV playback.
                scene(*palette[int(elapsed / 0.16) % len(palette)])
                if now >= next_pixel_flash:
                    next_pixel_flash = now + PIXEL_FLASH_S
                    for i in range(10):
                        # Independently choose one of seven nonblack RGB colors.
                        # Preserve the existing raw-channel current-budget cap.
                        rgb = palette[random.randrange(len(palette))]
                        pixels[i] = tuple(channel * PIXEL_CHANNEL_CAP for channel in rgb)
            pixels.show()            # ten pixels: ~300us data transfer, 25 times/s
        # Audio DMA and hardware PWM run in the background. No long sleeps or
        # blocking wait for audio completion; door input is checked every pass.
except BaseException:
    audio.stop()
    servo_pwm.duty_cycle = 0
    eye_red.duty_cycle = 0
    eye_blue.duty_cycle = 0
    scene(False, False, False)
    pixels.fill((0, 0, 0))
    pixels.show()
    raise
finally:
    audio.deinit()
    servo_pwm.deinit()
    eye_red.deinit()
    eye_blue.deinit()
    for handle, wav in recordings:
        wav.deinit()
        handle.close()
