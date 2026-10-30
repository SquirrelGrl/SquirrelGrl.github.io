# Drinking-mode audio

Source: user-supplied PartyMusic.mp3.
Selected source interval: 01:57.000 through 02:17.000 (20.000 seconds).
Output: drinking.wav, mono, 16,000 Hz, signed 16-bit uncompressed PCM, 320,000 frames.
Processing: -6 dB gain for initial playback headroom; 5 ms fade at each boundary to suppress wraparound clicks. No time stretching or crossfade; the full selected 20 seconds is retained. A rhythmically seamless musical transition is not guaranteed.

Copy drinking.wav into CIRCUITPY/audio/. Existing code.py already loops this file while the door is closed. On reopening/reclosing the door the recording restarts from this selected section's beginning.

This WAV uses approximately 640 KB (625 KiB), not the original 6.7 MB conversion. Check actual CIRCUITPY free space before adding the other track. 2 MB nominal board flash is not the same as available filesystem space.

interrupted.wav has not been supplied yet. The current program requires both files; it will stop at startup until a valid mono 16 kHz 16-bit PCM interrupted.wav is added. No dummy sound file has been substituted.

Audio format, duration, peak sample and zero-valued boundary samples were checked digitally. Actual CPX playback and total speaker/supply current still need bench verification; -6 dB digital gain does not guarantee the 200 mA speaker budget. Begin with the STEMMA volume potentiometer low.
