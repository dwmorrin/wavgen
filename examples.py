from wavlib import *

def program_select(program, args):
    """ select program """
    samples = None
    if program == 'tone':
        gen = EnvelopedOscillator(
            EnvelopeGenerator(args.duration),
            Oscillator(globals()[args.waveform], args.frequency, sample_rate=args.sample_rate))
        samples = gen.oscillate()
    if program == 'beats':
        samples = kick_snare()
    if program == 'vibrato':
        gen = EnvelopedOscillator(
            EnvelopeGenerator(args.duration),
            Oscillator(
                globals()[args.waveform],
                modulator=Oscillator(sin, 8),
                sample_rate=args.sample_rate
            )
        )
        samples = gen.oscillate()
    if program == 'two-tone':
        samples = two_tone(args.sample_rate, args.frequency, args.duration, 5)
    if program == 'two-tone-scale':
        samples = two_tone_ionian(args.sample_rate, args.frequency, args.duration)
    if program == 'constant':
        samples = [32767 for i in range(int(args.sample_rate * args.duration))]
    if program == 'slope':
        samples = slope(-32768, 32767, 10)
    if program == 'scale':
        osc = Oscillator(globals()[args.waveform], args.frequency, sample_rate=args.sample_rate)
        osc.sample_rate = args.sample_rate
        samples = ionian(args.loops, args.duration, osc)
    if program == 'delay':
        samples = delay_test(
            args.sample_rate, args.loops, args.frequency, args.duration, args.delay, args.feedback, globals()[args.waveform])
    if program == 'random':
        samples = random_melody(args.sample_rate, args.loops, args.duration)
    if samples is None:
        raise ValueError("unknown type")
    return [samples[:] for channels in range(args.channels)]
