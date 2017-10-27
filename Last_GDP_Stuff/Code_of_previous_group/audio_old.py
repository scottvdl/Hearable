def rt(IO,FORMATS,SWITCHES,VARS,FUNC,INSTANCES):
	
	from time import time, sleep, strftime, gmtime
	from numpy import array, fromstring, zeros, savetxt
	import alsaaudio
	import gain
	import filtering
	import envelope_extraction
	import compression
	import NR
	import numpy as np
	from scipy import signal
	
	import matplotlib.pyplot as plt  ##REMOVE
	
	#============#
	#            #
	#    ALSA    #
	#            #
	#============#
	
	inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NORMAL,IO['card'])
	inp.setchannels(IO['channels'])
	inp.setrate(IO['fs'])
	inp.setformat(FORMATS[IO['data_type']]['alsa'])
	inp.setperiodsize(IO['period_size'])
	
	out = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK,alsaaudio.PCM_NORMAL,IO['card'])
	out.setchannels(IO['channels'])
	out.setrate(IO['fs'])
	out.setformat(FORMATS[IO['data_type']]['alsa'])
	out.setperiodsize(IO['period_size'])
	
	#=======================#
	#                       #
	#    LOCAL VARIABLES    #
	#                       #
	#=======================#
	
	iptr = 0 # Pointer for ring buffer FIR method
	
	outputs = array([zeros(IO['period_size'])]*VARS['bands']) # Outputs for each frequency band
	c = array([zeros(IO['period_size'])]*VARS['bands']) # Buffers for each frequency band
	buffer = zeros(IO['period_size']) # Buffer for previous input samples
	
	NR_out = array([zeros(IO['period_size'])]*VARS['bands'])
	NR_env = array([zeros(IO['period_size'])]*VARS['bands'])
	NR_env0 = [0]*VARS['bands']
	
	bN = 7
	NR_buffer = array([zeros(IO['period_size']*bN)]*VARS['bands'])
	
	comp_out = array([zeros(IO['period_size'])]*VARS['bands'])
	comp_env = array([zeros(IO['period_size'])]*VARS['bands'])
	comp_env0 = [0]*VARS['bands']
	
	silence = chr(0)*IO['channels']*IO['period_size']*FORMATS[IO['data_type']]['bytes'] # Buffer filled with silence
	
	wait_time = IO['period_size']/IO['fs']
	
	#=================#
	#                 #
	#    FUNCTIONS    #
	#                 #
	#=================#
	
	class latencyMeasurement():
	
		def __init__(self,fs,N):
			self.fs = fs
			self.N = N
			self.data = []
		
		def time(self):
			self.T = time()
		
		def append(self):
			self.data.append(time()-self.T)
		
		def reset(self):
			self.data = []
		
		def export(self):
			self.data.append(self.N)
			self.data.append(self.fs)
			r = strftime("%Y-%m-%d %H:%M:%S", gmtime())
			print('# Saving latency measurements...')
			savetxt(r + ' test.txt',self.data)
	
	INSTANCES['latency'] = latencyMeasurement(IO['fs'],IO['period_size'])
	
	while SWITCHES['quit'] == False:
		
		if SWITCHES['audio'] == True:
		
			l,data = inp.read() # Find length and extract data from stream
			T1 = time()
			if l == IO['period_size']: # Check that the length is equal to the period_size length
				
				data_inp = fromstring(data,dtype=FORMATS[IO['data_type']]['numpy'])
				data_proc = data_inp
				
				if SWITCHES['latency'] == True: # If latency measurement are enabled, take timestamp
					INSTANCES['latency'].time()
				
				#==================#
				#                  #
				#    INPUT GAIN    #
				#                  #
				#==================#
				
				if SWITCHES['input_gain'] == True:
					
					gain.calculate(data_proc,VARS['input_gain'],IO['period_size'],data_proc)
				
				buffer = data_proc
				
				if SWITCHES['filtering'] == True:
					
					#========================#
					#                        #
					#    DECOMPOSE SIGNAL    #
					#                        #
					#========================#
					
					if VARS['filtering_method'] == 'FIR':
						outputs = filtering.fir(VARS['h'],data_proc,outputs,c,iptr,IO['period_size'],VARS['ntaps'])
						
					elif VARS['filtering_method'] == 'FFT':
						
						signal_fft = np.fft.rfft(np.append(last_input[IO['period_size']-VARS['ntaps']:IO['period_size']],data_proc),VARS['fft_size'])
						
						filter_delay = (VARS['ntaps']-1)/2;
						
						if SWITCHES['feedback_reduction'] == True:
							signal_fft_magnitude = np.absolute(signal_fft);
							max_index = np.argmax(signal_fft_magnitude[40:signal_fft_magnitude.size-5]) + 40;  #Peak in FFT (ignore very low and high freqs)
							#print(max_index)
							max_value = signal_fft_magnitude[max_index];
							#print(max_value)
							if max_value>np.mean(signal_fft_magnitude[40:signal_fft_magnitude.size-5]) + VARS['feedback_reduction_threshold']*np.std(signal_fft_magnitude[40:signal_fft_magnitude.size-5]):  # If there's a large peak
								center_freq = max_index*(1.0/(signal_fft_magnitude.size));
								#print(center_freq);
								h_notch = signal.firwin(VARS['ntaps'],[max(0.01,center_freq-VARS['feedback_reduction_bandwidth']/2), min(center_freq+VARS['feedback_reduction_bandwidth']/2,0.99)])
								h_notchfft = np.fft.rfft(h_notch,VARS['fft_size'])
								signal_fft = signal_fft*h_notchfft;
								filter_delay = VARS['ntaps']-1;
							
						o1 = np.fft.irfft(VARS['hfft'][0]*signal_fft)
						o2 = np.fft.irfft(VARS['hfft'][1]*signal_fft)
						o3 = np.fft.irfft(VARS['hfft'][2]*signal_fft)
						o4 = np.fft.irfft(VARS['hfft'][3]*signal_fft)
						o5 = np.fft.irfft(VARS['hfft'][4]*signal_fft)
						
						output1 = o1[VARS['ntaps']+filter_delay:IO['period_size']+VARS['ntaps']+filter_delay]*VARS['band1']['gain']
						output2 = o2[VARS['ntaps']+filter_delay:IO['period_size']+VARS['ntaps']+filter_delay]*VARS['band2']['gain']
						output3 = o3[VARS['ntaps']+filter_delay:IO['period_size']+VARS['ntaps']+filter_delay]*VARS['band3']['gain']
						output4 = o4[VARS['ntaps']+filter_delay:IO['period_size']+VARS['ntaps']+filter_delay]*VARS['band4']['gain']
						output5 = o5[VARS['ntaps']+filter_delay:IO['period_size']+VARS['ntaps']+filter_delay]*VARS['band5']['gain']
						
						outputs = np.array([output1,output2,output3,output4,output5])
					
					for i in xrange(0,VARS['bands']):
						
						#=======================#
						#                       #
						#    NOISE REDUCTION    #
						#                       #
						#=======================#
						
						if SWITCHES['band%i'%(i+1)]['NR'] == True:
							alphaA,alphaR = envelope_extraction.time_constants(IO['fs'],VARS['band%i'%(i+1)]['tauA_NR'],VARS['band%i'%(i+1)]['tauR_NR'])
							envelope_extraction.calculate(outputs[i],alphaA,alphaR,IO['period_size'],NR_env0[i],NR_env[i])
							NR_env0[i] = NR_env[i][IO['period_size']-1]
							NR_buffer[i][0:IO['period_size']] = NR_env[i]
							NR.wiener(IO['period_size'],NR_buffer[i],outputs[i],NR_out[i]) # New line
							outputs[i] = NR_out[i]
							NR_buffer[i][IO['period_size']:] = NR_buffer[i][0:IO['period_size']*(bN-1)]
						
						#===================#
						#                   #
						#    COMPRESSION    #
						#                   #
						#===================#
						
						if SWITCHES['band%i'%(i+1)]['comp'] == True:
							alphaA,alphaR = envelope_extraction.time_constants(IO['fs'],VARS['band%i'%(i+1)]['tauA_comp'],VARS['band%i'%(i+1)]['tauR_comp'])
							envelope_extraction.calculate(outputs[i],alphaA,alphaR,IO['period_size'],comp_env0[i],comp_env[i])
							comp_env0[i] = comp_env[i][IO['period_size']-1]
							compression.calculate(outputs[i],IO['period_size'],comp_env[i],VARS['band%i'%(i+1)]['T'],VARS['band%i'%(i+1)]['CR'],VARS['band%i'%(i+1)]['KW'],VARS['band%i'%(i+1)]['MG'],comp_out[i])
							outputs[i] = comp_out[i]
					
					#===============#
					#               #
					#    SOLOING    #
					#               #
					#===============#
					
					if SWITCHES['band1']['solo'] == True:
						data_proc = outputs[0]
					elif SWITCHES['band2']['solo'] == True:
						data_proc = outputs[1]
					elif SWITCHES['band3']['solo'] == True:
						data_proc = outputs[2]
					elif SWITCHES['band4']['solo'] == True:
						data_proc = outputs[3]
					elif SWITCHES['band5']['solo'] == True:
						data_proc = outputs[4]
					else:
						data_proc = outputs[0]+outputs[1]+outputs[2]+outputs[3]+outputs[4]
					
				data_proc = array(data_proc,dtype=FORMATS[IO['data_type']]['numpy'])
				
				#if SWITCHES['filtering'] == True:  #REMOVe
					#plt.plot(np.append(last_output,data_proc))
					#plt.hold(True)
					#plt.plot(np.append(last_input,data_inp))
					#plt.show()
					#break;
				
				if SWITCHES['latency'] == True: # If latency measurements are enabled, take second timestamp and write out latency
					INSTANCES['latency'].append()
				
				out.write(data_proc)
				last_input = data_inp
				#last_output=data_proc #REMOVE
				
			else:
				sleep(wait_time)
			
		else:
			out.write(silence)
	else:
		sleep(0.0001)