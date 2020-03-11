""" Direct Digital Synthesis """

from collections import namedtuple
from math import pi, sin, asin, tan, atan
from random import uniform

class DDS_Element:
    """ super element """
    def __init__(self, sample_rate):
        self.sample_rate = sample_rate

# waveform functions return float in range (-1.0,1.0)
# pylint: disable=unused-argument
def noise(x):
    """ takes arg for comptability with other funcs only """
    return uniform(-1, 1)

def saw(x):
    """ sawtooth """
    return (2/pi) * atan(tan(x))

def square(x):
    """ square """
    return -1 if sin(x) < 0 else 1

def tri(x):
    """ triangle """
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

# namedtuples for easier passing of parameters
# ADSR controls are in % of total time
ADSR_ctrl = namedtuple('ADSR_ctrl', 'attack decay sustain sustain_level release')

class EnvelopeGenerator(DDS_Element):
    """ applies envelopes to sample_lists """
    def __init__(self, period=1.0,
                 ctrl=ADSR_ctrl(0.1, 0, 0.8, 1, 0.1),
                 function=adsr, sample_rate=44100, master_level=1):
        super().__init__(sample_rate)
        if ctrl.attack + ctrl.decay + ctrl.sustain + ctrl.release != 1:
            raise ValueError("ADSR time fractions should add to 1")
        self.ctrl = ctrl
        self.function = function
        self.period = period
        self.ctrl_in_samples = self.calc_ctrl_in_samples()
        self.master_level = master_level

    def calc_ctrl_in_samples(self):
        """ changes % controls to number of samples """
        n_samples = self.period * self.sample_rate
        return ADSR_ctrl(
            self.ctrl.attack * n_samples, self.ctrl.decay * n_samples,
            self.ctrl.sustain * n_samples, self.ctrl.sustain_level,
            self.ctrl.release * n_samples
        )

    def amplitude(self, sample_list):
        """ scale a sample_list with the envelope """
        enveloped_list = sample_list[:]
        for i, _ in enumerate(enveloped_list):
            enveloped_list[i] = int(enveloped_list[i] * self.master_level * self.valueAtSample(i))
        return enveloped_list

    def valueAtSample(self, sample):
        """ public access for the envelope function """
        return self.function(sample, self.ctrl_in_samples)

class Oscillator(DDS_Element):
    """ wrapper for the elementary period functions """
    def __init__(self, function=sin, frequency=440, level=1, modulator=None, sample_rate=44100):
        super().__init__(sample_rate)
        self.function = function
        self.frequency = frequency
        self.level = level
        self.modulator = modulator

    def valueAtSample(self, sample):
        """ public access for the elementary period function, with modulation """
        mod = 0 if self.modulator is None else self.modulator.valueAtSample(sample)
        return self.function(sample*self.frequency*2*pi/self.sample_rate + mod)

    def oscillate(self, duration):
        """ returns list of samples """
        return [self.valueAtSample(sample) for sample in range(self.sample_rate * duration)]

class EnvelopedOscillator:
    """ combines E.G. and Oscillator for simple voice patches """
    def __init__(self, eg, osc, max_value=(2**16//2)):
        self.eg = eg
        self.osc = osc
        self.max_value = max_value

    def oscillate(self):
        """ do eg.amplitude(osc.oscillate(duration)) in one go """
        return [int(self.max_value * self.osc.valueAtSample(sample) * self.eg.valueAtSample(sample))
                for sample in range(int(self.osc.sample_rate * self.eg.period))]

# effects/filters
def delay(samples, sample_rate, time, feedback=0):
    """ returns a list of samples, same length as input """
    sample_delay = int(sample_rate * time)
    delay_ring = [0 for i in range(sample_delay)]
    record_head = 0
    mix = samples[:]
    for i, _ in enumerate(mix):
        playback_head = (record_head + 1) % sample_delay
        delay_ring[record_head] = mix[i] + int(delay_ring[playback_head] * feedback)
        mix[i] += delay_ring[playback_head]
        mix[i] //= 2
        record_head = playback_head
    return mix
