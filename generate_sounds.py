import numpy as np
import wave
import struct

def create_tone(filename, freq, duration_sec, volume=0.5, sample_rate=44100):
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), False)
    tone = np.sin(freq * 2 * np.pi * t) * volume

    with wave.open(filename, 'w') as wav_file:
        nchannels = 1
        sampwidth = 2
        framerate = sample_rate
        nframes = len(tone)
        comptype = "NONE"
        compname = "not compressed"
        wav_file.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))

        for s in tone:
            wav_file.writeframes(struct.pack('h', int(s * 32767)))

# Hit: short 800 Hz pop, 0.15 sec
create_tone("hit.wav", 800, 0.15)

# Combo: three 440 Hz beeps, 0.1 sec each with short gaps
def create_combo(filename):
    sample_rate = 44100
    beep_duration = 0.1
    silence_duration = 0.05
    total_duration = beep_duration*3 + silence_duration*2
    t = np.linspace(0, total_duration, int(sample_rate * total_duration), False)
    tone = np.zeros_like(t)

    beep_samples = int(beep_duration * sample_rate)
    silence_samples = int(silence_duration * sample_rate)
    freq = 440
    beep = np.sin(freq * 2 * np.pi * np.linspace(0, beep_duration, beep_samples, False)) * 0.5

    idx = 0
    for i in range(3):
        tone[idx:idx+beep_samples] = beep
        idx += beep_samples
        if i < 2:
            idx += silence_samples

    with wave.open(filename, 'w') as wav_file:
        nchannels = 1
        sampwidth = 2
        framerate = sample_rate
        nframes = len(tone)
        comptype = "NONE"
        compname = "not compressed"
        wav_file.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))

        for s in tone:
            wav_file.writeframes(struct.pack('h', int(s * 32767)))

create_combo("combo.wav")

# Record: 1.2 sec rising tone from 400 to 1000 Hz
def create_record(filename):
    sample_rate = 44100
    duration = 1.2
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    freqs = np.linspace(400, 1000, len(t))
    tone = np.sin(2 * np.pi * freqs * t) * 0.5

    with wave.open(filename, 'w') as wav_file:
        nchannels = 1
        sampwidth = 2
        framerate = sample_rate
        nframes = len(tone)
        comptype = "NONE"
        compname = "not compressed"
        wav_file.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))

        for s in tone:
            wav_file.writeframes(struct.pack('h', int(s * 32767)))

create_record("record.wav")

print("Audio files created: hit.wav, combo.wav, record.wav")
