# Living Toy Robot — Halloween Minifridge

Revision C · October 21, 2026

This design uses an **unmodified Adafruit Circuit Playground Express (CPX)**, two common-cathode RGB eye LEDs, **two** common-anode RGB scene LEDs, the existing Adafruit STEMMA Speaker PID 3885, an SG90, and a copper-tape door contact. It uses all ten factory NeoPixels. No external MOSFET, switching transistor, driver IC, expansion board, or capacitor is added.

**Approved requirement change:** the user requested removal of the separate red interruption LEDs and use of the scene RGB lighting for red on command. Accordingly, the separate interruption group has quantity **zero**, and D3–D4 supply steady red during interruption. This change reduces the external signal requirement from nine to eight. No slide-switch solder tap or CPX modification is used.

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

Scene effects use the seven nonblack combinations of the three channels. These are colorful timed rave changes, not continuously variable external scene fades. Eyes have true hardware PWM fades; the ten onboard pixels flash independently chosen random colors at five color changes per second while the door is closed. A4/PB03 and A5/PB02 are not assigned `PWMOut`; A7/PB08 is the input. This avoids assuming that every exposed CPX pad supports CircuitPython PWM.

## 2. GPIO and LED current verification — two scene LEDs

**D3 and D4 operate together.** Their red cathode branches share A3; green branches share A4; blue branches share A5. This uses three GPIO signals total, irrespective of LED count. Each element has its own resistor: no resistor is shared between LEDs. Both common anodes connect to CPX **3.3 V**, never 5 V or VOUT.

| Branches | References | Value | Quantity | Nominal current per element at 3.3 V |
|---|---|---:|---:|---:|
| Two eye red elements | R1, R3 | 2.2 kΩ | 2 | 0.591 mA, Vf = 2.0 V |
| Two eye blue elements | R2, R4 | 2.2 kΩ | 2 | 0.227 mA, Vf = 2.8 V |
| Two scene red elements | R5, R8 | 2.2 kΩ | 2 | 0.591 mA, Vf = 2.0 V |
| Two scene green elements | R6, R9 | 2.2 kΩ | 2 | 0.273 mA, Vf = 2.7 V |
| Two scene blue elements | R7, R10 | 2.2 kΩ | 2 | 0.227 mA, Vf = 2.8 V |

Resistor total: **ten 2.2 kΩ resistors** (four for the eyes and six for the scene LEDs), all 5% tolerance or better and at least 1/8 W. Revision C removes D5 and R11–R13 and changes scene resistors R5–R10 from 3.3 kΩ to 2.2 kΩ. Each remaining scene element receives **50% more nominal current** than in revision B, with the same combined GPIO current. Actual perceived brightness depends on the LED and surroundings; it is not guaranteed to rise by exactly 50%.

`I = max(0, (Vrail − Vf − GPIO drop) / R)`. Nominal maximum external LED current is **3.818 mA** with all elements on. This neglects GPIO voltage drop; actual current and brightness will generally be lower. The exact LED part numbers are unknown. The conservative check below assumes Vrail = 3.63 V, resistor minimum = 95% of nominal, and minimum Vf = 1.6 V red, 2.0 V green, 2.4 V blue. These are design assumptions, not measured characteristics.

| GPIO | Combined nominal current | Combined conservative maximum | Normal-drive loading target |
|---|---:|---:|---:|
| A1 — two eye red branches | 1.182 mA source | 1.943 mA source | Below 2 mA source |
| A2 — two eye blue branches | 0.455 mA source | 1.177 mA source | Below 2 mA source |
| A3 — two scene red branches | 1.182 mA sink | 1.943 mA sink | Below 2.5 mA sink |
| A4 — two scene green branches | 0.545 mA sink | 1.560 mA sink | Below 2.5 mA sink |
| A5 — two scene blue branches | 0.455 mA sink | 1.177 mA sink | Below 2.5 mA sink |
| All external LEDs | 3.818 mA | **7.799 mA** | Sum of all ten elements |

Worst-case red scene calculation: `2 × (3.63 − 1.6) / (2200 × 0.95) = 1.943 mA` on A3. Total worst-case external sourcing is 3.120 mA; sinking is 4.679 mA. These remain far below the SAMD21 I/O-cluster ceilings of **46 mA source / 65 mA sink**, even pessimistically assigning all source current to one cluster and all sink current to one cluster. Reserve a further 5 mA for onboard logic/pull-ups. Door pull-up is at most about 0.182 mA under the assumptions used previously.

The commonly advertised 7 mA GPIO recommendation / 10 mA maximum are not operating targets here. Adafruit's SAMD21 pinout documentation gives **130 mA absolute maximum for the package**. A deliberately conservative 50 mA allowance for MCU plus factory support circuitry, all 7.799 mA external LED current, and 5 mA logic margin totals **62.8 mA**, below that ceiling. NeoPixel supply current flows through the regulator rail, not its data GPIO; servo and speaker motor/amplifier power do not flow through GPIO.

The largest calculated resistor dissipation is an eye red resistor at approximately **1.972 mW**; scene red resistors dissipate about **1.972 mW each**, well below 125 mW. The actual LED parts must satisfy the stated minimum-Vf assumptions. Two scene LEDs provide more current per element than revision B’s three-LED arrangement, while retaining the same combined current budget. High-Vf green/blue parts may be dim at 3.3 V. Check appearance with the actual parts; do not lower resistors or move anodes to 5 V without redesigning the current limits.

## 3. Series versus parallel wiring

Each active LED element and its own resistor form a **series branch**. Matching-color branches are connected **in parallel** at their shared GPIO.

* Eyes: A1 splits through R1 and R3 to the two red anodes; A2 splits through R2 and R4 to the two blue anodes. Both common cathodes go to GND. Green leads remain unconnected and individually insulated.
* Scene red: D3 red cathode → R5 → A3; D4 red cathode → R8 → A3.
* Scene green: D3 green cathode → R6 → A4; D4 green cathode → R9 → A4.
* Scene blue: D3 blue cathode → R7 → A5; D4 blue cathode → R10 → A5.
* D3 and D4 common anodes all connect to CPX 3.3 V. GPIO LOW turns that color on across both packages; HIGH turns it off. The two packages show the same color together.

Do not place the two LEDs in series, and do not put bare parallel elements behind one shared resistor. RGB physical lead order varies: the schematic uses logical R/common/G/B pin numbers; identify the actual leads using their datasheets or a diode test.

## 4. Power topology and budget

Use an appropriate **regulated 5.0 V, 3 A supply**, distributed in two branches with a common ground:

1. A USB power lead to the CPX's normal USB connector. The schematic's `USB VBUS` pin is that connector's 5 V input, **not the VOUT pad**. Use one power source; no concurrent battery or second powered USB lead.
2. Separate short power and return wires directly from the supply to SG90 red (+5 V) and brown/black (GND). Connect its orange/yellow signal to A6. Do not power the servo from CPX 3.3 V or VOUT, or pass its current through the CPX ground lead.

Connect CPX **VOUT → STEMMA POWER**, **A0 → SIG**, and **GND → GND**. VOUT is derived through CPX's factory power path and can be below 5 V; PID 3885 accepts 3–5 V. Its factory amplifier and coupling capacitors are already present. No additional amplifier or capacitor is fitted.

| Load | Design allowance | Route |
|---|---:|---|
| CPX MCU and factory support circuitry | 50 mA | CPX USB / internal regulator |
| Ten NeoPixels at firmware raw-channel cap 12 | 38.3 mA | CPX internal 3.3 V rail |
| External LED branches | 7.8 mA | CPX 3.3 V rail / GPIO |
| Door pull-up | 0.2 mA | CPX 3.3 V rail |
| **CPX, excluding external speaker** | **96.3 mA** | USB branch |
| STEMMA Speaker at adjusted volume | **200 mA allowance** | VOUT |
| **Planned CPX USB branch total** | **296.3 mA** | Below 350 mA measured acceptance target |
| SG90 startup/load/stall allowance | **1,000 mA** | Direct supply branch |
| **Combined design allowance** | **1,296.3 mA** | 3 A supply provides headroom |

NeoPixel estimate: `10 × (1 mA idle + 3 × 20 mA × 12/255) = 38.24 mA`, including a conservative full-white command at the code's cap. Actual patterns generally use fewer active channels. Current pulses still occur inside the pixels; the factory board's existing supply components remain necessary. The CPX hardware schematic identifies an AP2112K-3.3 regulator and a **500 mA resettable fuse** in its power path. The regulator's nominal capability is not permission to overheat it or bypass the fuse. At approximately 97 mA on 3.3 V, estimated regulator dissipation is around 0.12–0.17 W depending on actual input voltage.

**Supply-current verification is a commissioning measurement, not something ERC can perform.** PID 3885's 1 W speaker rating does not ensure a 200 mA input limit. Start with its onboard volume potentiometer at minimum, use normalized recordings at reduced level, then measure the entire CPX USB branch during the loudest passage with all effects active. Keep it **at or below 350 mA**, and keep the speaker branch at or below its 200 mA allowance. A 500 mA fuse is not a precision current regulator. At 1 W acoustic-driver electrical output and 85% amplifier efficiency, 4.5 V input would already imply about 261 mA, so unrestricted full volume is outside this design budget.

SG90 clones vary; 1 A is a planning allowance, not a guaranteed maximum. Measure startup and loaded travel for the actual servo, use a supply that remains regulated, and verify that the head never binds or holds a mechanical end stop. The 3.3 V control signal is commonly accepted by SG90 units, but this must be checked on the actual unit because no traceable servo part/datasheet was supplied. No capacitor or level shifter has been silently added. With the no-added-capacitor constraint, wiring length and supply transient response matter: failure to hold voltage during movement is a commissioning failure requiring supply/wiring correction within the approved topology.

## 5. CircuitPython and actual recorded audio

Install the current stable **CircuitPython build specifically for Circuit Playground Express**.

**Running from Thonny:** save the file as `code.py` in the root of CIRCUITPY, click the Shell, then press **Control+D** (or press the board Reset button once). Avoid Run/F5 or `%Run -c $EDITOR_CONTENT` on this RAM-limited board: sending the whole editor text can require extra memory. Close any other serial console first.

The compact application keeps **one WAV file and one WaveFile object open at a time**, closes and releases them before changing tracks, reuses one **512-byte** double buffer, and collects garbage between tracks. It prints free RAM at startup for diagnosis. It no longer preloads three audio objects or imports `math`; eye fading uses a triangle wave. This reduces source size and expected runtime allocation, but actual RAM headroom must be checked on the board. A short track handoff can still occur while opening a new file. The application imports only `board`, `digitalio`, `pwmio`, `audioio`, `audiocore`, `neopixel`, `gc`, `random`, and `time`. CPX builds normally include/freeze `neopixel`; if your build does not, install the matching official CircuitPython `neopixel.mpy` library. No driver hardware is required.

Copy `code.py` and the included `audio` directory to CIRCUITPY. All three selected recordings are now included:

* `audio/drinking.wav`: PartyMusic.mp3 excerpt 1:57–2:17, 20 seconds, looped during drinking mode.
* `audio/record_scratch.wav`: full decoded RecordScratch.m4a, approximately 0.858 seconds, played once when the door opens.
* `audio/radio_static.wav`: full decoded RadioStatic.mp3, approximately 6.502 seconds, looped after scratch until the door closes.

All files are **mono, uncompressed PCM, 16-bit signed, 16,000 Hz**. The combined WAV size is **875,630 bytes (855.1 KiB)**. They stream from flash rather than loading fully into the CPX's 32 kB RAM. CPX has 2 MB nominal external flash, but actual filesystem capacity/free space depends on firmware and installed files. Check available CIRCUITPY space before copying. Copy only code, needed libraries and the three WAV files; keep schematic/PDF/ZIP files on your computer. `interrupted.wav` is no longer used.

Digital audio was attenuated by 6 dB and given 5 ms boundary fades to suppress clicks. No time stretching or generated-tone substitute is used. Output format, frame counts, non-silence and sample levels were checked digitally. These checks do not establish perceived loudness or safe amplifier current; adjust the existing volume pot and verify the current budget on hardware. Detailed audio notes and exact sizes are in `audio/README.md` and `audio/Audio-validation.json`. All three files are mandatory; missing or invalid files stop the program when that track is first requested.

AudioOut uses the DAC, background DMA, and an available timer. Hardware eye PWM uses separate TCC0 and TCC1 channels; servo uses TC4. Constructing the servo before AudioOut prevents the audio allocator from claiming TC4. Digital scene outputs use no timer. NeoPixel writes for ten pixels take approximately 300 µs plus protocol overhead and occur at 25 Hz. These peripheral allocations support concurrency architecturally; hardware playback/dropout testing is still required. Flash I/O and garbage collection can introduce short delays, so this is responsive cooperative control, not a hard-real-time guarantee.

Door closed: contact LOW, servo approaches 40°, eyes fade blue↔purple, both scene LEDs cycle seven RGB combinations together, and all ten pixels flash random nonblack colors five times per second while the drinking WAV loops. Door open: after 35 ms of stable input, current audio stops, RecordScratch plays once and then RadioStatic loops, servo approaches 110°, eyes become red, both scene LEDs become steady red, and all ten pixels stay solid red. Door closed again restores the drinking mode and **restarts the drinking recording from its beginning**, rather than resuming its previous sample offset. Animation and servo updates use monotonic deadlines without waiting for audio completion.

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
