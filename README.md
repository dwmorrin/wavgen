### wavegen

Utility for generating .wav files.

```shell
usage: wavgen.py [-h] [-d DURATION] [-f FREQUENCY] [-o FILENAME]
                 [-r SAMPLE_RATE] [-w WAVEFORM] [-t TYPE]

Generate .wav file using direct digital synthesis

optional arguments:
  -h, --help            show this help message and exit
  -d DURATION, --duration DURATION
                        duration of tone
  -f FREQUENCY, --frequency FREQUENCY
                        audio frequency
  -o FILENAME, --output FILENAME
                        output filename
  -r SAMPLE_RATE, --rate SAMPLE_RATE
                        sample rate
  -w WAVEFORM, --waveform WAVEFORM
                        sin|tri|saw|square
  -t TYPE, --type TYPE  tone|constant|scale|slope|two-tone|two-tone-
                        scale|delaytest
```
