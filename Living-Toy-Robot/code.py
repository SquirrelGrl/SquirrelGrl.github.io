# CPX robot: one streamed WAV at a time; no extra hardware or libraries.
import gc
import time
import random
import board
import digitalio
import pwmio
import audioio
import audiocore
import neopixel

gc.collect()
print('Robot starting; free RAM:', gc.mem_free())
CAP = 12
DRINK_ANGLE = 40.0
VIEWER_ANGLE = 110.0
DEBOUNCE = 0.035
# Seven nonblack colors; shared by scene and onboard random flashes.
COLORS = ((1,0,0),(0,1,0),(0,0,1),(1,1,0),(0,1,1),(1,0,1),(1,1,1))
PATHS = ('/audio/drinking.wav', '/audio/record_scratch.wav', '/audio/radio_static.wav')

def output(pin, value):
    p = digitalio.DigitalInOut(pin)
    p.switch_to_output(value=value)
    return p

mute = output(board.SPEAKER_ENABLE, False)
status = output(board.LED, False)
r = output(board.A3, True)
g = output(board.A4, True)
b = output(board.A5, True)
door = digitalio.DigitalInOut(board.A7)
door.switch_to_input(pull=digitalio.Pull.UP)
red = pwmio.PWMOut(board.A1, frequency=1000, duty_cycle=0)
blue = pwmio.PWMOut(board.A2, frequency=1000, duty_cycle=0)
servo = pwmio.PWMOut(board.A6, frequency=50, duty_cycle=0)
pixels = neopixel.NeoPixel(board.NEOPIXEL, 10, brightness=1.0, auto_write=False)
pixels.fill((0,0,0))
pixels.show()
audio = audioio.AudioOut(board.A0)
# Reuse one double buffer. Never keep all three files/WaveFiles open.
buffer = bytearray(512)
handle = None
wav = None

def close_wave():
    global handle, wav
    audio.stop()
    if wav is not None:
        wav.deinit()
        wav = None
    if handle is not None:
        handle.close()
        handle = None

def play(index):
    global handle, wav
    close_wave()
    gc.collect()
    handle = open(PATHS[index], 'rb')
    wav = audiocore.WaveFile(handle, buffer)
    if wav.channel_count != 1 or wav.sample_rate != 16000 or wav.bits_per_sample != 16:
        raise ValueError('WAV must be mono 16kHz 16-bit PCM')
    audio.play(wav, loop=(index != 1))

def scene(color):
    r.value = not color[0]
    g.value = not color[1]
    b.value = not color[2]

def angle(value):
    servo.duty_cycle = int((1000 + 1000 * value / 180) * 50 * 65535 / 1000000)

now = time.monotonic()
raw = bool(door.value)
changed = now
opened = True
ready = False
scratch = False
position = VIEWER_ANGLE
target = position
mode_start = now
frame_at = now
servo_at = now
flash_at = now
try:
    angle(position)
    gc.collect()
    print('Hardware ready; free RAM:', gc.mem_free())
    while True:
        now = time.monotonic()
        reading = bool(door.value)
        if reading != raw:
            raw = reading
            changed = now
        if now - changed >= DEBOUNCE and (not ready or opened != raw):
            opened = raw
            ready = True
            mode_start = now
            target = VIEWER_ANGLE if opened else DRINK_ANGLE
            scratch = opened
            if opened:
                red.duty_cycle = 65535
                blue.duty_cycle = 0
                scene(COLORS[0])
                pixels.fill((CAP,0,0))
                pixels.show()
            play(1 if opened else 0)
            frame_at = now
            flash_at = now
        if ready and opened and scratch and not audio.playing:
            scratch = False
            play(2)
        if now >= servo_at:
            servo_at = now + 0.02
            position += max(-2.0, min(2.0, target - position))
            angle(position)
        if ready and now >= frame_at:
            frame_at = now + 0.04
            elapsed = now - mode_start
            if opened:
                red.duty_cycle = 65535
                blue.duty_cycle = 0
                scene(COLORS[0])
                pixels.fill((CAP,0,0))
            else:
                phase = elapsed % 4
                red.duty_cycle = int((phase if phase < 2 else 4 - phase) * 32767.5)
                blue.duty_cycle = 65535
                scene(COLORS[int(elapsed / 0.16) % 7])
                if now >= flash_at:
                    flash_at = now + 0.20
                    for i in range(10):
                        c = COLORS[random.randrange(7)]
                        pixels[i] = (c[0]*CAP, c[1]*CAP, c[2]*CAP)
            pixels.show()
finally:
    close_wave()
    servo.duty_cycle = 0
    red.duty_cycle = 0
    blue.duty_cycle = 0
    scene((0,0,0))
    pixels.fill((0,0,0))
    pixels.show()
    audio.deinit()
    servo.deinit()
    red.deinit()
    blue.deinit()
