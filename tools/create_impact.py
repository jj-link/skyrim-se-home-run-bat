#!/usr/bin/env python3
"""Generate the original Home Run Bat one-shot using only Python's standard library.

Provenance: all audio is synthesized here from oscillators and seeded noise;
there are no recordings, third-party samples, melodies, or input audio files.
In particular, assets/audio/homerun_screech.mp3 is not read or incorporated.
Run from any directory: python tools/create_impact.py
"""

import array
import hashlib
import json
import math
from pathlib import Path
import random
import sys
import wave


SAMPLE_RATE = 44_100
DURATION = 0.48
OUTPUT = Path(__file__).resolve().parents[1] / "Data/Sound/fx/HomeRunBat/impact.wav"


def synthesize():
    """A short woody crack/body, with a quieter upward air accent; never looped."""
    rng = random.Random(0x484F4D4552554E)
    samples = []
    air_low = 0.0
    previous_input = 0.0
    previous_output = 0.0
    # Inharmonic, rapidly damped wood modes, not a pitched musical chord.
    modes = ((437.0, 0.57, 0.047), (1139.0, 0.31, 0.025),
             (2167.0, 0.17, 0.013), (3521.0, 0.08, 0.007))
    for index in range(round(SAMPLE_RATE * DURATION)):
        t = index / SAMPLE_RATE
        attack = 1.0 - math.exp(-t / 0.00045)
        wood = sum(level * math.sin(math.tau * frequency * t)
                   * math.exp(-t / decay)
                   for frequency, level, decay in modes)
        # Low, briefly dropping body gives mass without a long explosive boom.
        body_phase = math.tau * (112.0 * t + 18.0 * 0.024
                                 * (1.0 - math.exp(-t / 0.024)))
        body = 0.48 * math.sin(body_phase) * math.exp(-t / 0.033)
        noise = rng.uniform(-1.0, 1.0)
        crack = 0.32 * noise * math.exp(-t / 0.006)
        value = attack * (wood + body + crack)

        # A subdued 235 ms ascending air flick follows, not a sustained whistle.
        air_low += 0.16 * (noise - air_low)
        u = t - 0.045
        if 0.0 < u < 0.235:
            envelope = math.sin(math.pi * u / 0.235) ** 2
            phase = math.tau * (640.0 * u + 0.5 * 3700.0 * u * u)
            value += envelope * (0.028 * math.sin(phase) + 0.052 * air_low)

        # DC blocker, followed by a smooth final fade to exact digital silence.
        filtered = value - previous_input + 0.995 * previous_output
        previous_input, previous_output = value, filtered
        fade = min(1.0, max(0.0, (DURATION - 0.001 - t) / 0.035))
        fade = fade * fade * (3.0 - 2.0 * fade)
        samples.append(filtered * fade)

    # Linear normalization leaves 2 dB of sample headroom; no clipping/limiter.
    gain = 10.0 ** (-2.0 / 20.0) / max(abs(value) for value in samples)
    return array.array("h", (round(value * gain * 32767) for value in samples))


def inspect(path):
    """Read back the delivered WAV, not just the floating-point synth buffer."""
    with wave.open(str(path), "rb") as audio:
        channels = audio.getnchannels()
        width = audio.getsampwidth()
        rate = audio.getframerate()
        frames = audio.getnframes()
        compression = audio.getcomptype()
        payload = audio.readframes(frames)
    pcm = array.array("h")
    pcm.frombytes(payload)
    if sys.byteorder != "little":
        pcm.byteswap()
    normalized = [value / 32768.0 for value in pcm]
    peak = max(abs(value) for value in normalized)
    rms = math.sqrt(sum(value * value for value in normalized) / len(pcm))
    tail = normalized[-round(rate * 0.02):]
    return {
        "path": str(path),
        "format": f"PCM signed {width * 8}-bit little-endian",
        "compression": compression,
        "channels": channels,
        "sample_rate_hz": rate,
        "frames": frames,
        "duration_seconds": frames / rate,
        "peak_dbfs": round(20.0 * math.log10(peak), 4),
        "peak_sample": max(abs(value) for value in pcm),
        "rms_dbfs": round(20.0 * math.log10(rms), 4),
        "dc_mean": sum(normalized) / len(pcm),
        "clipped_samples": sum(value <= -32768 or value >= 32767 for value in pcm),
        "first_sample": pcm[0],
        "last_sample": pcm[-1],
        "final_20ms_peak": max(abs(value) for value in tail),
        "max_adjacent_delta": max(abs(b - a) for a, b in zip(pcm, pcm[1:])),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def main():
    pcm = synthesize()
    if sys.byteorder != "little":
        pcm.byteswap()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUTPUT), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(SAMPLE_RATE)
        audio.writeframes(pcm.tobytes())
    print(json.dumps(inspect(OUTPUT), indent=2))


if __name__ == "__main__":
    main()
