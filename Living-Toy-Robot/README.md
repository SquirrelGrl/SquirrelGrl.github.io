# Living Toy Robot — Halloween Minifridge

Revision A · October 21, 2026

This design uses an **unmodified Adafruit Circuit Playground Express (CPX)**, two common-cathode RGB eye LEDs, **one** common-anode RGB scene LED, the existing Adafruit STEMMA Speaker PID 3885, an SG90, and a copper-tape door contact. It uses all ten factory NeoPixels. No external MOSFET, switching transistor, driver IC, expansion board, or capacitor is added.

**Approved requirement change:** the user requested removal of the separate red interruption LEDs and use of the scene RGB lighting for red on command. Accordingly, the separate interruption group has quantity **zero**, and D3 supplies steady red during interruption. This change reduces the external signal requirement from nine to eight. No slide-switch solder tap or CPX modification is used.

## Files

* `Living Toy Robot.kicad_sch`: editable, native KiCad 9 schematic.
* `Living Toy Robot.kicad_pro`, `LivingToyRobot.kicad_sym`, `sym-lib-table`: project and complete-module symbols. Keep together. Open the project first; standard KiCad symbol libraries must be installed.
* `Living Toy Robot.pdf`, `Living Toy Robot.svg`: printable/vector exports of that schematic.
* `IO-table.csv`, `Wiring-table.csv`, `LED-branches.csv`, `Power-budget.csv`: complete assembly tables.
* `code.py`: CircuitPython application using streamed PCM WAV playback, hardware servo/eye PWM, and nonblocking animation deadlines.
* `ERC-report.txt`: actual KiCad electrical rules check, with no exclusions added.
* `Validation-report.txt`: software simulation and netlist verification results, with hardware limitations stated.

The CPX and STEMMA symbols represent the **complete existing products**, not bare ICs. Their factory internal circuitry, including capacitors and amplifiers, is not new hardware. J1 denotes the supply's existing two-wire output/distribution point; it does not require an additional board or a purchased connector. No PCB/footprint design is implied.

## 1. Signal count and controller decision

| Function | Independent external signals | Implementation |
|---|---:|---|
| External recorded audio | 1 | A0 analog DAC |
| Eye red | 1 | A1 PWM; two individually resisted branches |
| Eye blue | 1 | A2 PWM; two individually resisted branches |
| Scene red, green, blue | 3 | A3, A4, A5; active-low digital RGB combinations |
| Servo | 1 | A6 hardware PWM, 50 Hz |
| Door contact | 1 | A7 digital input with internal pull-up |
| Separate interruption LEDs | 0 | Removed by explicit user revision; scene red supplies the effect |
| Ten onboard NeoPixels | 0 external | Existing D8 / PB23 and factory wiring |
| **Total** | **8** | Exactly A0–A7 |

The two eyes share a red command and a blue command. Red and blue brightness are independently adjustable, but the left and right eyes do not animate independently. The original requirements explicitly permit parallel matching-color branches.

Before the user revision, CPX's eight accessible pads could not accommodate all nine independent functions. Reducing the number of interruption LEDs alone would reduce current, not the signal count. A Pico W or Feather M4 Express has enough accessible signals for the original external groups, but neither retains ten CPX factory NeoPixels as a single-board replacement. Pico W also lacks a native DAC; its audio path would require a separately verified PWM-audio implementation. Feather M4 Express has DAC outputs and adequate GPIO, but does not provide the requested ten onboard pixels. Extra pins never authorize extra current per pin. After the approved revision, neither replacement nor a second MCU is necessary; the final controller is CPX.

Scene effects use the seven nonblack combinations of the three channels. These are colorful timed rave changes, not continuously variable external scene fades. Eyes have true hardware PWM fades; the ten onboard pixels supply smooth rainbow, chase, and pulse animation. A4/PB03 and A5/PB02 are not assigned `PWMOut`; A7/PB08 is the input. This avoids assuming that every exposed CPX pad supports CircuitPython PWM.

## 2. GPIO and LED current verification

Use these resistor values, **5% tolerance or better**, rated at least 1/8 W:

| Branches | References | Value | Quantity | Nominal branch current at 3.3 V |
|---|---|---:|---:|---:|
| Eye 1 red; eye 2 red | R1; R3 | 2.2 kΩ | 2 | 0.591 mA each, assuming Vf = 2.0 V |
| Eye 1 blue; eye 2 blue | R2; R4 | 2.2 kΩ | 2 | 0.227 mA each, assuming Vf = 2.8 V |
| Scene red | R5 | 1.0 kΩ | 1 | 1.300 mA, assuming Vf = 2.0 V |
| Scene green | R6 | 1.0 kΩ | 1 | 0.600 mA, assuming Vf = 2.7 V |
| Scene blue | R7 | 1.0 kΩ | 1 | 0.500 mA, assuming Vf = 2.8 V |

`I = max(0, (Vrail − Vf − GPIO drop) / R)`. The table conservatively omits the GPIO drop for maximum-current estimates; real current and brightness will be lower. Nominal total with every enabled LED element at full duty is **4.036 mA**. A1 sources 1.182 mA total and A2 sources 0.455 mA total.

The supplied LED part numbers and measured forward voltages are unknown. The following conservative electrical check uses **Vrail = 3.63 V**, resistor minimum 95% of nominal, and minimum Vf of 1.6 V red, 2.0 V green, and 2.4 V blue. These are stated design assumptions, not fabricated measured characteristics.

| Output | Worst-case continuous current | Comparison |
|---|---:|---|
| A1, two red eye branches | 1.943 mA source | Below conservative 2 mA normal-drive source loading |
| A2, two blue eye branches | 1.177 mA source | Below 2 mA source loading |
| A3, scene red | 2.137 mA sink | Below conservative 2.5 mA normal-drive sink loading |
| A4, scene green | 1.716 mA sink | Below 2.5 mA sink loading |
| A5, scene blue | 1.295 mA sink | Below 2.5 mA sink loading |
| **All external LED branches** | **8.267 mA** | 3.120 mA source plus 5.147 mA sink |

The SAMD21's commonly advertised 7 mA GPIO recommendation and 10 mA maximum are **not** design targets. This design stays below the lower normal-drive loading above, without needing to change the output-strength register. Even pessimistically assigning all external source current to one I/O cluster and all external sink current to one cluster leaves ample margin against the SAMD21's **46 mA source / 65 mA sink per-cluster limits**. Door pull-up current is at most approximately 3.63 V / 20 kΩ = **0.182 mA**; servo control and speaker SIG are signal loads, not their power loads. Allow an additional 5 mA GPIO margin for factory-board logic and pull-ups; source and sink remain far below the cluster limits.

Adafruit's SAMD21 pinout documentation specifies **130 mA absolute maximum for the package**. Budgeting 50 mA for MCU plus factory support circuitry, then pessimistically adding all 8.267 mA external LED current and 5 mA logic allowance, gives **63.3 mA**, below that ceiling. This deliberately overcounts some current and does not treat all 3.3 V rail current as MCU pin current. NeoPixels take their LED current from the regulator rail, not through the NeoPixel data GPIO. Likewise, servo and STEMMA amplifier power never flows through GPIO pins.

The actual LED parts must fit the stated minimum Vf assumptions. Maximum resistor dissipation under those assumptions is scene red: `(3.63 − 1.6)^2 / 950 = 4.34 mW`, well below 125 mW. Even a direct 3.63 V across a 950 Ω resistor is under 14 mW. Very high-Vf green/blue LEDs may be dim at 3.3 V; verify their appearance before assembly. Do not reduce resistors or move scene anodes to 5 V to compensate. Without external drivers, modest brightness is the intended tradeoff.

## 3. Series versus parallel wiring

Each enabled LED element and **its own resistor** form one series branch. The order of resistor and LED within a branch can be exchanged without changing current, but the supplied schematic and wiring table define one specific arrangement.

* A1 splits into **R1 → D1 red anode** and **R3 → D2 red anode**. D1/D2 common cathodes return to GND.
* A2 splits into **R2 → D1 blue anode** and **R4 → D2 blue anode**. These are two parallel branches, not two bare LEDs behind one shared resistor.
* D3 common anode connects to **CPX 3.3 V**. Each cathode goes through its own resistor to its own GPIO: red/R5/A3, green/R6/A4, blue/R7/A5. LOW sinks current and turns that element on. HIGH turns it off.
* Eye green anodes are unconnected and insulated separately. They are not grounded or tied to other colors.

Do not wire two LEDs in series from a 3.3 V GPIO: there is insufficient voltage headroom, particularly for blue. Do not connect common-cathode eyes as common-anode devices. Physical RGB lead order varies: the schematic uses logical R/common/G/B pin numbers, and the actual components must be identified with their datasheets or a diode test.

## 4. Power topology and budget

Use an appropriate **regulated 5.0 V, 3 A supply**, distributed in two branches with a common ground:

1. A USB power lead to the CPX's normal USB connector. The schematic's `USB VBUS` pin is that connector's 5 V input, **not the VOUT pad**. Use one power source; no concurrent battery or second powered USB lead.
2. Separate short power and return wires directly from the supply to SG90 red (+5 V) and brown/black (GND). Connect its orange/yellow signal to A6. Do not power the servo from CPX 3.3 V or VOUT, or pass its current through the CPX ground lead.

Connect CPX **VOUT → STEMMA POWER**, **A0 → SIG**, and **GND → GND**. VOUT is derived through CPX's factory power path and can be below 5 V; PID 3885 accepts 3–5 V. Its factory amplifier and coupling capacitors are already present. No additional amplifier or capacitor is fitted.

| Load | Design allowance | Route |
|---|---:|---|
| CPX MCU and factory support circuitry | 50 mA | CPX USB / internal regulator |
| Ten NeoPixels at firmware raw-channel cap 12 | 38.3 mA | CPX internal 3.3 V rail |
| External LED branches | 8.3 mA | CPX 3.3 V rail / GPIO |
| Door pull-up | 0.2 mA | CPX 3.3 V rail |
| **CPX, excluding external speaker** | **96.8 mA** | USB branch |
| STEMMA Speaker at adjusted volume | **200 mA allowance** | VOUT |
| **Planned CPX USB branch total** | **296.8 mA** | Below 350 mA measured acceptance target |
| SG90 startup/load/stall allowance | **1,000 mA** | Direct supply branch |
| **Combined design allowance** | **1,296.8 mA** | 3 A supply provides headroom |

NeoPixel estimate: `10 × (1 mA idle + 3 × 20 mA × 12/255) = 38.24 mA`, including a conservative full-white command at the code's cap. Actual patterns generally use fewer active channels. Current pulses still occur inside the pixels; the factory board's existing supply components remain necessary. The CPX hardware schematic identifies an AP2112K-3.3 regulator and a **500 mA resettable fuse** in its power path. The regulator's nominal capability is not permission to overheat it or bypass the fuse. At approximately 97 mA on 3.3 V, estimated regulator dissipation is around 0.12–0.17 W depending on actual input voltage.

**Supply-current verification is a commissioning measurement, not something ERC can perform.** PID 3885's 1 W speaker rating does not ensure a 200 mA input limit. Start with its onboard volume potentiometer at minimum, use normalized recordings at reduced level, then measure the entire CPX USB branch during the loudest passage with all effects active. Keep it **at or below 350 mA**, and keep the speaker branch at or below its 200 mA allowance. A 500 mA fuse is not a precision current regulator. At 1 W acoustic-driver electrical output and 85% amplifier efficiency, 4.5 V input would already imply about 261 mA, so unrestricted full volume is outside this design budget.

SG90 clones vary; 1 A is a planning allowance, not a guaranteed maximum. Measure startup and loaded travel for the actual servo, use a supply that remains regulated, and verify that the head never binds or holds a mechanical end stop. The 3.3 V control signal is commonly accepted by SG90 units, but this must be checked on the actual unit because no traceable servo part/datasheet was supplied. No capacitor or level shifter has been silently added. With the no-added-capacitor constraint, wiring length and supply transient response matter: failure to hold voltage during movement is a commissioning failure requiring supply/wiring correction within the approved topology.

## 5. CircuitPython and actual recorded audio

Install the current stable **CircuitPython build specifically for Circuit Playground Express**. The application imports only `board`, `digitalio`, `pwmio`, `audioio`, `audiocore`, `neopixel`, `math`, and `time`. CPX builds normally include/freeze `neopixel`; if your build does not, install the matching official CircuitPython `neopixel.mpy` library. No driver hardware is required.

Copy `code.py` to CIRCUITPY. Create an `audio` directory containing:

* `drinking.wav`: your recorded mad-scientist drinking track.
* `interrupted.wav`: your recorded scary electronic track.

**Recordings were not supplied, and this package does not invent or include recordings.** The delivered source performs real file-based WAV playback through A0; it never substitutes generated tones. Both files are mandatory and fail visibly if missing or in the wrong format. Export each as **mono, uncompressed PCM, 16-bit signed, 16,000 Hz**. With ffmpeg, for example: `ffmpeg -i input.wav -ac 1 -ar 16000 -c:a pcm_s16le output.wav`. Adjust content amplitude/normalize without clipping and set physical amplifier volume during the current check above.

CPX has 2 MB nominal external flash, with firmware/filesystem overhead. At 32,000 bytes/s, a 15-second file occupies approximately 480 kB; two such tracks total approximately 960 kB. Check actual CIRCUITPY free space rather than assuming the entire flash is available. WAVs stream from flash; they are not fully loaded into CPX's 32 kB RAM. Starting with 10–15 seconds per recording leaves practical space for code and filesystem overhead.

AudioOut uses the DAC, background DMA, and an available timer. Hardware eye PWM uses separate TCC0 and TCC1 channels; servo uses TC4. Constructing the servo before AudioOut prevents the audio allocator from claiming TC4. Digital scene outputs use no timer. NeoPixel writes for ten pixels take approximately 300 µs plus protocol overhead and occur at 25 Hz. These peripheral allocations support concurrency architecturally; hardware playback/dropout testing is still required. Flash I/O and garbage collection can introduce short delays, so this is responsive cooperative control, not a hard-real-time guarantee.

Door closed: contact LOW, servo approaches 40°, eyes fade blue↔purple, scene cycles seven RGB combinations, and all ten pixels run a rainbow/chase/pulse pattern while the drinking WAV loops. Door open: after 35 ms of stable input, current audio stops, the scary WAV loops, servo approaches 110°, eyes become red, scene becomes steady red, and pixels alternate red/purple at 2 Hz. Door closed again restores the drinking mode and **restarts the drinking recording from its beginning**, rather than resuming its previous sample offset. Animation and servo updates use monotonic deadlines without waiting for audio completion.

The servo retains a hardware holding pulse at its target. Travel is about 70° under nominal pulse calibration; adjust the two angle constants with the horn unloaded, then fit the mechanism. Software ramps by at most 2° every 20 ms. At boot, interrupted mode is the safe logical default, with audio starting after the initial debounce interval. An open/broken door wire reads as interrupted.

## 6. Build and validation boundaries

KiCad ERC checks the schematic at the module terminals. It cannot certify LED brightness, the actual servo's logic threshold/stall current, regulator temperature, acoustic quality, or timing on a physical board. The included validation report distinguishes automated checks from unperformed bench measurements. No physical CPX, LED parts, supply, speaker, or servo was connected to this environment.

Before loading the head mechanism: identify LED leads; continuity-check power and ground; check 3.3 V and VOUT polarity; prove the servo can accept the 3.3 V signal; load the two actual recordings; verify the power/current targets above; and exercise door bounce, repeated open/close events during playback, and the full approximately 70° travel. Keep all wiring and electronics isolated from minifridge mains wiring and moving mechanisms.

## References and evidence

* Adafruit CPX original hardware source, including power fuse, regulator, exposed GPIO and ten 3.3 V NeoPixels: https://github.com/adafruit/Adafruit-Circuit-Playground-Express-PCB
* Official CircuitPython CPX pin aliases: https://github.com/adafruit/circuitpython/blob/main/ports/atmel-samd/boards/circuitplayground_express/pins.c
* Official SAMD peripheral timer mappings: https://github.com/adafruit/samd-peripherals/blob/main/samd/samd21/pins.c
* Official PWM resource allocation: https://github.com/adafruit/circuitpython/blob/main/ports/atmel-samd/common-hal/pwmio/PWMOut.c
* Official DAC audio implementation: https://github.com/adafruit/circuitpython/blob/main/ports/atmel-samd/common-hal/audioio/AudioOut.c
* PID 3885 manufacturer description and schematic (3–5 V, integrated amplifier, 1 W / 8 Ω speaker): https://github.com/adafruit/Adafruit-STEMMA-Speaker-PCB
* SAMD21 family electrical characteristics, Microchip DS40001882: https://ww1.microchip.com/downloads/en/DeviceDoc/SAM-D21-DA1-Family-Data-Sheet-DS40001882.pdf — use the DC characteristics/drive-strength conditions and I/O cluster limitations, not an aggregate current figure alone. The PDF itself could not be retrieved in this session; low-drive figures are conservative design assumptions corroborated by published datasheet excerpts, not a claim of a fresh full-datasheet audit.
* Manufacturer SAMD21 pin/package current guidance (same MCU family): https://github.com/adafruit/Adafruit-Feather-M0-Adalogger-PCB/blob/master/Adafruit_Feather_M0_Adalogger_Pinout.svg
* SparkFun SAMD21 cluster-current documentation: https://github.com/sparkfun/Graphical_Datasheets/blob/master/Datasheets/SAM21/SamMini.csv

The exact LED, servo, and power-supply part specifications remain user-hardware-dependent. The circuit is a complete buildable low-current topology under the stated component assumptions; it is not a claim that unknown existing components have been bench-qualified.
