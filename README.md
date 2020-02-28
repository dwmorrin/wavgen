### wavegen

Utility for generating .wav files.

```shell
usage: wavgen.py [-h] [-c CHANNELS] [--delay DELAY] [-d DURATION]
                 [--feedback FEEDBACK] [-f FREQUENCY] [-l LOOPS] [-o FILENAME]
                 [-r SAMPLE_RATE] [--sampwidth SAMPWIDTH] [-w WAVEFORM]
                 [-t TYPE]

Generate .wav file using direct digital synthesis

optional arguments:
  -h, --help            show this help message and exit
  -c CHANNELS, --channels CHANNELS
                        channel count
  --delay DELAY         delay time
  -d DURATION, --duration DURATION
                        duration of tone
  --feedback FEEDBACK   range 0.0 to 1.0, delay feedback
  -f FREQUENCY, --frequency FREQUENCY
                        audio frequency
  -l LOOPS, --loops LOOPS
                        loops/repeats (depends on type)
  -o FILENAME, --output FILENAME
                        output filename
  -r SAMPLE_RATE, --rate SAMPLE_RATE
                        sample rate
  --sampwidth SAMPWIDTH
                        sample width, 16 bit = 2
  -w WAVEFORM, --waveform WAVEFORM
                        sin|tri|saw|square
  -t TYPE, --type TYPE  tone|constant|scale|slope|two-tone|two-tone-
                        scale|delaytest|vibrato|random
```
