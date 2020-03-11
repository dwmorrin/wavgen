#!/usr/bin/env python3
""" generate .wav file containing test tone """
import argparse
import wave

from wavlib import write_samples
import examples

parser = argparse.ArgumentParser(
        description="Generate .wav file using direct digital synthesis")
parser.add_argument('-c', '--channels', help="channel count", type=int, default=1)
parser.add_argument('--delay', help="delay time", type=float, default=0.2)
parser.add_argument('-d', '--duration', help="duration of tone", type=float, default=1)
parser.add_argument('--feedback', help="range 0.0 to 1.0, delay feedback", type=float, default=0.3)
parser.add_argument('-f', '--frequency', help="audio frequency", type=int, default=440)
parser.add_argument('-l', '--loops', help="loops/repeats (depends on type)", type=int, default=1)
parser.add_argument('-o', '--output', help="output filename", dest='filename', default="tone.wav")
parser.add_argument('-r', '--rate', help="sample rate", dest='sample_rate', type=int, default=44100)
parser.add_argument('--sampwidth', help="sample width, 16 bit = 2", type=int, default=2)
parser.add_argument('-w', '--waveform', help="sin|tri|saw|square|noise", default='sin')
parser.add_argument('program', help="see examples.py for choices")
args = parser.parse_args()

wav_file = wave.open(args.filename, "wb")
wav_file.setnchannels(args.channels)
wav_file.setsampwidth(args.sampwidth)
wav_file.setframerate(args.sample_rate)
write_samples(wav_file, *examples.program_select(args.program, args))
wav_file.close()
