#!/usr/bin/env python
import alsaaudio, time, numpy



chunk = 256 # Buffer size (128/fs = 8ms)
channels = 1
card = 'plughw:1,0' # Audio input/output source
fs = 12000 # Sampling frequency


""" INPUT """
inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NORMAL,card)
inp.setchannels(channels)
inp.setrate(fs)
inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
inp.setperiodsize(chunk)

""" OUTPUT """
out = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK,alsaaudio.PCM_NORMAL,card)
out.setchannels(channels)
out.setrate(fs)
out.setformat(alsaaudio.PCM_FORMAT_S16_LE)
out.setperiodsize(chunk)

silence = chr(0)*channels*chunk*2 # silence work around for incorrect chunk size

                  
""" The global variable 'start' communicates
between the GUI & playback threads """


""" Main playback function """
def play():
    while not finish:
        if start == 1:
                l,data = inp.read()
                
                if l == chunk: # Avoid writing incorrect data length out
                    
                    numpydata = numpy.fromstring(data, dtype = numpy.int16)
                    
                    out.write(ndata.astype(numpydata.int16))       
                else:
                    out.write(silence)
        else:
            pass
        time.sleep(0.001)


finish = False
start = 1


play()

