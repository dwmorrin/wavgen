""" Glue for DDS and Wave """

from math import pi
from random import randint
from struct import pack

from dds import *

def byte16(short_int):
    """ formats signed 16 bit short_int to 2x 8 bits """
    if short_int > 32767 or short_int < -32768:
        raise ValueError(str(short_int) + ' is beyond signed 16 bit range')
    return pack("<h", short_int)

def interleave(*sample_lists):
    """ each sample_lists arg is a list of ordered 1 channel sample_lists """
    return [sample for frame in zip(*sample_lists) for sample in frame]

def scale(x, amplitude=0.5, master=0.8):
    """ converts [-1, 1] to 16 bit range """
    return round(x * 32767 * amplitude * master)

def rads_per_sample(frequency, sample_rate):
    """
    radians               1 second    frequency cycles    2pi radians
    -------- = -------------------- x ---------------- x  -----------
    sample      sample_rate samples             second        cycle
    """
    return frequency * 2 * pi / sample_rate

def write_samples(wav_write, *sample_lists):
    """ write samples from lists """
    for sample in interleave(*sample_lists):
        wav_write.writeframesraw(byte16(sample))

# USE DDS OSCILLATE METHODS INSTEAD
#def waveform(sample_rate, duration, oscillator):
#    """ returns a list of function values at a fixed frequency """
#    n_samples = int(sample_rate * duration)
#    sample_list = []
#    if oscillator.sample_rate != sample_rate:
#        raise ValueError("sample rates do not agree")
#    for sample in range(n_samples):
#        sample_list.append(scale(oscillator.valueAtSample(sample), 1))
#    return sample_list

def divider_test():
    """ testing using bpm for rhythm """
    bpm = 120
    division = 1
    duration = 60 / (bpm * division)
    eg = EnvelopeGenerator(duration)
    osc = EnvelopedOscillator(eg, Oscillator(sin, 440))
    samples = []
    for _ in range(4):
        samples += osc.oscillate()
    division = 2
    duration = 60 / (bpm * division)
    eg.period = duration
    eg.ctrl_in_samples = eg.calc_ctrl_in_samples()
    for _ in range(4):
        samples += osc.oscillate()
    return samples

def kick_snare():
    """ test of simple kick and snare patches """
    bpm = 120
    division = 1
    duration = 60 / (bpm * division)
    drum_env = ADSR_ctrl(.001, .5, 0, 0, 1 - (.5 + .001))
    kick_eg = EnvelopeGenerator(duration, drum_env)
    snare_eg = EnvelopeGenerator(duration, drum_env, master_level=.3)
    kick = EnvelopedOscillator(kick_eg, Oscillator(sin, 30))
    snare = EnvelopedOscillator(snare_eg, Oscillator(noise))
    samples = []
    for _ in range(2):
        samples += kick.oscillate()
        samples += snare.oscillate()
    return samples

def ionian(loops, note_duration, osc):
    """ returns list of samples playing an ionian (major) scale """
    gen = EnvelopedOscillator(EnvelopeGenerator(note_duration), osc)
    semitone_ratio = 2**(1/12)
    skip = [1, 3, 6, 8, 10] # black keys
    samples = []
    initial_frequency = osc.frequency
    for _ in range(loops):
        osc.frequency = initial_frequency
        for i in range(13):
            osc.frequency *= semitone_ratio
            if i not in skip:
                samples += gen.oscillate()
    return samples

def random_melody(sample_rate, loops, duration):
    """ meandering notes """
    def interval_ratio(interval):
        return 2**(interval/12)
    gen = EnvelopedOscillator(
        EnvelopeGenerator(duration),
        Oscillator(sin, 440, sample_rate=sample_rate))
    samples = []
    for _ in range(loops):
        gen.osc.frequency *= interval_ratio(randint(-18, 18))
        if gen.osc.frequency < 55:
            gen.osc.frequency = 110
        if gen.osc.frequency > 12000:
            gen.osc.frequency = 880 * 2
        samples += gen.oscillate()
    return samples

def slope(start, stop, n_samples):
    """ a series of samples with constant slope """
    inc = (stop - start) // n_samples
    return range(start, stop, inc)

def two_tone(sample_rate, frequency, duration, interval):
    """ returns list with a mix of two frequencies """
    eg = EnvelopeGenerator(duration)
    interval_ratio = 2**(interval/12)
    osc = Oscillator(sin, frequency, sample_rate=sample_rate)
    gen = EnvelopedOscillator(eg, osc)
    f1 = gen.oscillate()
    osc.frequency *= interval_ratio
    f2 = gen.oscillate()
    for i, _ in enumerate(f1):
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


def delay_test(sample_rate, loops, start_frequency, note_duration, delay_time, feedback, waveform):
    """ test of delay effect """
    osc = Oscillator(waveform, start_frequency)
    test = ionian(loops, note_duration, osc)
    eg = EnvelopeGenerator(len(test)/sample_rate)
    return eg.amplitude(delay(test, sample_rate, delay_time, feedback))
