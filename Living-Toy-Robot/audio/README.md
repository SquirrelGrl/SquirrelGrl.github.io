# Robot audio — ready to copy

Copy this audio directory (containing the three WAV files) and code.py to CIRCUITPY. Do not copy the entire hardware ZIP or schematic files onto the microcontroller. The three WAV files total **875,630 bytes / 855.1 KiB**; code and filesystem overhead require additional space. Check actual CIRCUITPY free space. An obsolete interrupted.wav, if present, is no longer used and can be removed.

| File | Source | Output duration | Behavior |
|---|---|---:|---|
| drinking.wav | PartyMusic.mp3, 01:57–02:17 | 20.000 s | Loop while door closed |
| record_scratch.wav | Full RecordScratch.m4a | 0.8576875 s | Play once per door opening |
| radio_static.wav | Full RadioStatic.mp3 | 6.501625 s | Loop after scratch, until door closes |

MP3/AAC container padding can make the source file's reported duration slightly longer than the decoded audio. Neither new effect has been deliberately cropped. All outputs are mono, uncompressed signed 16-bit PCM at 16,000 Hz. They use -6 dB digital gain, with 5 ms boundary fades and zero-valued first/last samples to suppress clicks. The music keeps the full selected 20 seconds. No time stretching or musical crossfade is applied.

## Sequence

Door opens after the 35 ms debounce: stop music, play scratch once, then begin looping static as soon as AudioOut reports scratch completion. There is no programmed pause and no blocking wait. CircuitPython scheduling and peripheral restart may introduce a short handoff gap; sample-perfect gapless playback has not been verified on hardware.

Door closes during either scratch or static: stop that sound and restart the drinking loop. If the door opens again, scratch plays again before static. Booting with the door already open also starts with scratch.

The software expects all three files at the exact lowercase paths /audio/drinking.wav, /audio/record_scratch.wav, /audio/radio_static.wav. Missing/incorrect-format files cause a visible setup failure, not a generated tone fallback.

See Audio-validation.json for checked frame counts, size and peak samples. Non-silence, format, unclipped output and boundary samples were checked digitally. Door interruption of both stages was simulated. Actual CPX RAM headroom, playback quality, handoff latency and supply current must still be checked on the board. Begin with the existing STEMMA volume control low; digital attenuation does not itself guarantee the 200 mA speaker budget.
