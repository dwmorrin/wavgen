#!/usr/bin/env python3
""" generate .wav file containing test tone """
from math import floor, pi, sin, asin, tan, atan
from struct import pack
import argparse
import wave

parser = argparse.ArgumentParser(
        description="Generate .wav file using direct digital synthesis")
parser.add_argument('-d', '--duration', help="duration of tone",
        dest='duration', type=float, default=1, action='store')
parser.add_argument('-f', '--frequency', help="audio frequency",
        dest='frequency', type=int, default=440, action='store')
parser.add_argument('-o', '--output', help="output filename",
        dest='filename', default="tone.wav", action='store')
parser.add_argument('-r', '--rate', help="sample rate",
        dest='sample_rate', type=int, default=44100, action='store')
parser.add_argument('-w', '--waveform', help="sin|tri|saw|square",
        dest='waveform', default='sin', action='store')
parser.add_argument('-t', '--type', help="tone|constant|scale|slope",
        dest='type', default='tone', action='store')
args = parser.parse_args()

MAX_VALUE = 32767

def byte16(int):
    """ formats signed 16 bit int to 2x 8 bits """
    if int > MAX_VALUE or int < -MAX_VALUE:
        raise ValueError
    return pack("<h", int)

def scale(x, amplitude=0.5, master=0.8):
    return round(x * MAX_VALUE * amplitude * master)

def saw(x):
    return (2/pi) * atan(tan(x))

def square(x):
    return -1 if sin(x) < 0 else 1

def tri(x):
    return (2/pi) * asin(sin(x))

"""
radians               1 second    frequency cycles    2pi radians
-------- = -------------------- x ---------------- x  -----------
sample      sample_rate samples             second        cycle

"""
def rads_per_sample(frequency, sample_rate):
    return frequency * 2 * pi / sample_rate

def write_samples(wav_write, value_list):
    """ write samples from a list """
    for sample in value_list:
        wav_write.writeframesraw(byte16(sample))

def write_waveform(wav_write, sample_rate, frequency, duration, func=sin, fade_in_duration=0.01, fade_out_duration=0.01):
    """ writes the given function at a fixed frequency with fade in/out """
    n_samples = int(sample_rate * duration)
    n_fade_in_end = int(sample_rate * fade_in_duration)
    n_fade_out_samples = int(sample_rate * fade_out_duration)
    n_fade_out_start = n_samples - n_fade_out_samples
    
    angle_rate = rads_per_sample(frequency, sample_rate)
    amplitude = 0.0
    fade_in_inc = 1/float(n_fade_in_end)
    fade_out_dec = 1/float(n_fade_out_samples)
    samples = []
    for sample in range(n_samples):
        if sample <= n_fade_in_end:
            amplitude += fade_in_inc
        if sample >= n_fade_out_start:
            amplitude -= fade_out_dec
        samples.append(scale(func(sample*angle_rate), amplitude))
    write_samples(wav_write, samples)

def ionian(wav_write, loops, start_freq, note_duration):
    """ play an ionian (major) scale """
    semitone_ratio = 2**(1/12)
    skip = [1, 3, 6, 8, 10] # black keys
    for x in range(loops):
        f = start_freq
        for i in range(13):
            f *= semitone_ratio
            if i not in skip:
                write_waveform(wav_write, args.sample_rate, f, note_duration, globals()[args.waveform])

def slope(wav_write, start, stop, n_samples):
    """ generates a series of samples with constant slope """
    inc = (stop - start) // n_samples
    write_samples(wav_write, range(start, stop, inc))

wav_file = wave.open(args.filename, "wb")
wav_file.setnchannels(1)
wav_file.setsampwidth(2)
wav_file.setframerate(args.sample_rate)

if args.type == 'tone':
    write_waveform(wav_file, args.sample_rate, args.frequency, args.duration,
            globals()[args.waveform])
elif args.type == 'constant':
    write_samples(wav_file,
            [MAX_VALUE for i in range(int(args.sample_rate * args.duration))])
elif args.type == 'slope':
    slope(wav_file, -MAX_VALUE, MAX_VALUE, 10)
elif args.type == 'scale':
    ionian(wav_file, 2, args.frequency, 0.5)

wav_file.close()
