#!/usr/bin/env python3
""" generate .wav file containing test tone """
import argparse
from collections import namedtuple
from math import floor, pi, sin, asin, tan, atan
import random
from struct import pack
import wave

parser = argparse.ArgumentParser(
        description="Generate .wav file using direct digital synthesis")
parser.add_argument('-c', '--channels', help="channel count",
        type=int, default=1)
parser.add_argument('--delay', help="delay time",
        type=float, default=0.2)
parser.add_argument('-d', '--duration', help="duration of tone",
        type=float, default=1)
parser.add_argument('--feedback', help="range 0.0 to 1.0, delay feedback",
        type=float, default=0.3)
parser.add_argument('-f', '--frequency', help="audio frequency",
        type=int, default=440)
parser.add_argument('-l', '--loops', help="loops/repeats (depends on type)",
        type=int, default=1)
parser.add_argument('-o', '--output', help="output filename",
        dest='filename', default="tone.wav")
parser.add_argument('-r', '--rate', help="sample rate",
        dest='sample_rate', type=int, default=44100)
parser.add_argument('--sampwidth', help="sample width, 16 bit = 2",
        type=int, default=2)
parser.add_argument('-w', '--waveform', help="sin|tri|saw|square|noise",
        default='sin')
parser.add_argument('-t', '--type', help="tone|constant|scale|slope|two-tone|two-tone-scale|delaytest|vibrato|random",
        default='tone')
args = parser.parse_args()

if args.feedback < 0.0 or args.feedback > 1.0:
    raise ValueError(str(args.feedback) + ' is beyond 0.0 to 1.0 range')

MAX_VALUE = 32767

def byte16(int):
    """ formats signed 16 bit int to 2x 8 bits """
    if int > MAX_VALUE or int < -MAX_VALUE:
        raise ValueError(str(int) + ' is beyond signed 16 bit range')
    return pack("<h", int)

def interleave(*samples):
    """ each samples arg is a list of ordered 1 channel samples """
    return [sample for frame in zip(*samples) for sample in frame] 
def scale(x, amplitude=0.5, master=0.8):
    return round(x * MAX_VALUE * amplitude * master)

# namedtuples for easier passing of parameters
ADSR_ctrl = namedtuple('ADSR_ctrl', 'attack decay sustain sustain_level release')

# waveform functions return float in range (-1.0,1.0)
def noise(x):
    """ takes arg for comptability with other funcs only """
    return random.uniform(-1, 1)

def saw(x):
    return (2/pi) * atan(tan(x))

def square(x):
    return -1 if sin(x) < 0 else 1

def tri(x):
    return (2/pi) * asin(sin(x))

def adsr(t, ctrl):
    """ periodic ADSR envelope generator """
    if ctrl.sustain_level < 0 or ctrl.sustain_level > 1:
        raise ValueError("sustain_level out of range [0,1]")
    period = ctrl.attack + ctrl.decay + ctrl.sustain + ctrl.release
    t %= period
    if t < ctrl.attack:
        return (1/ctrl.attack)*(t-ctrl.attack)+1
    if t < ctrl.attack + ctrl.decay:
        return ((ctrl.sustain_level-1)/ctrl.decay)*(t-ctrl.attack)+1
    if t < ctrl.attack + ctrl.decay + ctrl.sustain:
        return ctrl.sustain_level
    release_start = ctrl.attack + ctrl.decay + ctrl.sustain
    return (-ctrl.sustain_level/ctrl.release)*(t-release_start) + ctrl.sustain_level

"""
radians               1 second    frequency cycles    2pi radians
-------- = -------------------- x ---------------- x  -----------
sample      sample_rate samples             second        cycle

"""
def rads_per_sample(frequency, sample_rate):
    return frequency * 2 * pi / sample_rate

def write_samples(wav_write, *sample_lists):
    """ write samples from lists """
    for sample in interleave(*sample_lists):
        wav_write.writeframesraw(byte16(sample))

def envelope(samples, sample_rate, ctrl):
    """ apply envelope to samples """
    if ctrl.attack + ctrl.decay + ctrl.sustain + ctrl.release != 1:
        raise ValueError("ADSR time fractions should add to 1")
    enveloped = samples[:]
    nsamples = len(samples)
    ctrl_in_samples = ADSR_ctrl(
            ctrl.attack * nsamples, ctrl.decay * nsamples,
            ctrl.sustain * nsamples, ctrl.sustain_level,
            ctrl.release * nsamples
            )
    for i, value in enumerate(samples):
        enveloped[i] *= adsr(i, ctrl_in_samples)
        enveloped[i] = int(enveloped[i])
    return enveloped


def waveform(sample_rate, frequency, duration, func=sin, fm_func=sin, fm_amp=0, fm_freq=8):
    """ returns a list of function values at a fixed frequency with fade in/out """
    n_samples = int(sample_rate * duration)
    samples = []
    for sample in range(n_samples):
        mod = fm_amp * fm_func(sample*fm_freq*2*pi/sample_rate)
        value = func(sample*frequency*2*pi/sample_rate + mod)
        samples.append(scale(value, 1))
    return samples

def ionian(sample_rate, loops, start_freq, note_duration, func=sin):
    """ returns list of samples playing an ionian (major) scale """
    semitone_ratio = 2**(1/12)
    skip = [1, 3, 6, 8, 10] # black keys
    samples = []
    for x in range(loops):
        f = start_freq
        for i in range(13):
            f *= semitone_ratio
            if i not in skip:
                samples += waveform(
                    sample_rate, f, note_duration, func)
    return samples

def random_melody(sample_rate, loops, duration):
    def interval_ratio(interval):
        return 2**(interval/12)
    frequency = 440
    samples = []
    for i in range(loops):
        frequency *= interval_ratio(random.randint(-18,18))
        if frequency < 55:
            frequency = 110
        if frequency > 12000:
            frequency = 880 * 2
        samples += waveform(sample_rate, frequency, duration)
    return samples

def slope(wav_write, start, stop, n_samples):
    """ writes a series of samples with constant slope """
    inc = (stop - start) // n_samples
    write_samples(wav_write, range(start, stop, inc))

def two_tone(sample_rate, frequency, duration, interval):
    """ returns list with a mix of two frequencies """
    interval_ratio = 2**(interval/12)
    f1 = waveform(sample_rate, frequency, duration)
    f2 = waveform(sample_rate, frequency * interval_ratio, duration)
    for i in range(len(f1)):
        f1[i] += f2[i]
        f1[i] = round(f1[i]/2)
    return f1

def two_tone_ionian(sample_rate, frequency, duration):
    """ write a fixed tone mixed with an major scale """
    skip = [1, 3, 6, 8, 10] # black keys
    samples = []
    for i in range(13):
        if i not in skip:
            samples += two_tone(sample_rate, frequency, duration, i)
    return samples

# effects/filters
def delay(samples, sample_rate, time, feedback=0):
    """ returns a list of samples, same length as input """
    sample_delay = int(sample_rate * time)
    delay_ring = [0 for i in range(sample_delay)]
    record_head = 0
    mix = samples[:]
    for i in range(len(mix)):
        playback_head = (record_head + 1) % sample_delay 
        delay_ring[record_head] = mix[i] + int(delay_ring[playback_head] * feedback)
        mix[i] += delay_ring[playback_head]
        mix[i] //= 2
        record_head = playback_head
    return mix

def delay_test(sample_rate, loops, start_frequency, note_duration, delay_time, feedback):
    test = ionian(sample_rate, loops, start_frequency, note_duration)
    return delay(test, sample_rate, delay_time, feedback)

def env_test(sample_rate, frequency, duration, func):
    tone = waveform(sample_rate, frequency, duration, func)
    env = ADSR_ctrl(.25, .25, .25, .25, .25)
    return envelope(tone, sample_rate, env)

# end defs; begin script

wav_file = wave.open(args.filename, "wb")
wav_file.setnchannels(args.channels)
wav_file.setsampwidth(args.sampwidth)
wav_file.setframerate(args.sample_rate)

if args.type == 'tone':
    tone = waveform(args.sample_rate, args.frequency, args.duration, globals()[args.waveform])
    ctrl = ADSR_ctrl(0.01, 0, args.duration - 0.02, 1, 0.01)
    enveloped = envelope(tone, args.sample_rate, env)
    samples = [enveloped[:] for channels in range(args.channels)]
    write_samples(wav_file, *samples)
elif args.type == 'env':
    tone = env_test(args.sample_rate, args.frequency, args.duration, globals()[args.waveform])
    samples = [tone[:] for channels in range(args.channels)]
    write_samples(wav_file, *samples)
elif args.type == 'vibrato':
    write_samples(wav_file,
           waveform(args.sample_rate, args.frequency, args.duration, globals()[args.waveform], .01, .01, sin, .3, 8))
elif args.type == 'two-tone':
    write_samples(wav_file,
           two_tone(args.sample_rate, args.frequency, args.duration, 5))
elif args.type == 'two-tone-scale':
   write_samples(wav_file, two_tone_ionian(args.sample_rate, args.frequency, args.duration))
elif args.type == 'constant':
    write_samples(wav_file,
            [MAX_VALUE for i in range(int(args.sample_rate * args.duration))])
elif args.type == 'slope':
    slope(wav_file, -MAX_VALUE, MAX_VALUE, 10)
elif args.type == 'scale':
    write_samples(wav_file, ionian(args.sample_rate, args.loops, args.frequency, 0.5))
elif args.type == 'delaytest':
    write_samples(wav_file, delay_test(
        args.sample_rate, args.loops, args.frequency, args.duration, args.delay, args.feedback))
elif args.type == 'random':
    write_samples(wav_file, random_melody(args.sample_rate, args.loops, args.duration))

wav_file.close()
