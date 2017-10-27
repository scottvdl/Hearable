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

def rt(IO,FORMATS,SWITCHES,VARS,FUNC,INSTANCES):
	
	#============#
	#    ALSA    #
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
	
	#====================================#
	#    DEFINE FUNCTIONS AND CLASSES    #
	#====================================#
	
	class latencyMeasurement():
		
		"""
		
		DESCRIPTION
		Object for performing, storing and exporting latency measurements
		
		INPUTS
		fs		Sampling frequenct of the signal
		N		Period size of the signal
		
		METHODS
		time	Gets current timestamp
		append	Append time (in seconds) since last time()
		export	Export data to .txt file
		reset	Empty data array
		
		"""
		
		def __init__(self,fs,N):
			self.fs = fs
			self.N = N
			self.data = []
		
		def time(self): # Get time
			self.T = time()
		
		def append(self): # Append time (in s) since last .time() to data array
			self.data.append(time()-self.T)
		
		def export(self):
			self.data.append(self.N)
			self.data.append(self.fs)
			r = strftime('%Y-%m-%d %H:%M:%S', gmtime())
			print('# Saving latency measurements...')
			savetxt(r + ' test.txt',self.data)
		
		def reset(self):
			self.data = []
	
	class countdown():
		
		"""
		
		DESCRIPTION
		Object for turning on modules in sequency
		
		INPUTS
		fs		Sampling frequenct of the signal
		N		Period size of the signal
		
		METHODS
		time	Gets current timestamp
		append	Append time (in seconds) since last time()
		export	Export data to .txt file
		reset	Empty data array
		
		"""
		
		
		def __init__(self, list,wait):
			self.list = list
			self.wait = wait
			self.split = False
			self.start = False
		
		def go(self):
			print('# Countdown started! Please wait...')
			self.start = True
			self.t1 = time()
			self.i = 0
			self.band = 1
		
		def update(self):
			if self.start == True:
				if self.i < len(self.list):
					self.t2 = time()
					if self.t2 - self.t1 > self.wait/1000.0:
						self.t1 = time()
						if self.split == False:
							print('# Turning on %s'%(self.list[self.i]))
							SWITCHES[self.list[self.i]] = True
							if self.list[self.i] == 'filtering':
								self.split = True
							self.i += 1
						elif self.split == True:
							SWITCHES['band%i'%(self.band)][self.list[self.i]] = True
							print('# Turning on band %i %s'%(self.band,self.list[self.i]))
							self.band +=1
							if self.band > VARS['bands']:
								self.i += 1
								self.band = 1
				else:
					self.start = False
					print('# Countdown complete!')
	
	#========================#
	#    CREATE INSTANCES    #
	#========================#
	
	INSTANCES['latency'] = latencyMeasurement(IO['fs'],IO['period_size'])
	INSTANCES['countdown'] = countdown(['audio','input_gain','filtering','NR','comp'],500)
	
	#=======================#
	#    LOCAL VARIABLES    #
	#=======================#
	
	# Filtering
	iptr = 0 # Pointer for ring buffer FIR method
	c = array([zeros(IO['period_size'])]*VARS['bands']) # Buffers for each frequency band
	data_before_filtering = zeros(IO['period_size']) # Buffer for previous input samples
	o = array([zeros(VARS['fft_size'])]*VARS['bands']) # Output array for FFT method
	outputs = array([zeros(IO['period_size'])]*VARS['bands']) # Outputs for each frequency band
	
	# Noise reduction
	NR_out = array([zeros(IO['period_size'])]*VARS['bands'])
	NR_env = array([zeros(IO['period_size'])]*VARS['bands'])
	NR_env0 = [0]*VARS['bands']
	bN = 7
	NR_buffer = array([zeros(IO['period_size']*bN)]*VARS['bands'])
	
	# Compression
	comp_out = array([zeros(IO['period_size'])]*VARS['bands'])
	comp_env = array([zeros(IO['period_size'])]*VARS['bands'])
	comp_env0 = [0]*VARS['bands']
	
	# ALSA
	silence = chr(0)*IO['channels']*IO['period_size']*FORMATS[IO['data_type']]['bytes'] # Buffer filled with silence
	wait_time = IO['period_size']/IO['fs']
	
	# Saving of input/output
	L = round(VARS['data_collection_length']*IO['fs'])
	input_array = zeros(L)
	output_array = zeros(L)
	SWITCHES['write_out'] = False
	
	#========================#
	#    AUDIO PROCESSING    #
	#========================#
	
	while SWITCHES['quit'] == False: # While not quitting
		
		INSTANCES['countdown'].update()
		
		if SWITCHES['audio'] == True: # If audio is turned on
		
			l,data = inp.read() # Find length and extract data from stream
			
			if l == IO['period_size']: # Check that the length is equal to the period_size length
				
				data_inp = fromstring(data,dtype=FORMATS[IO['data_type']]['numpy'])
				data_proc = data_inp
				
				if SWITCHES['collect_data'] == True: # If data collection is enabled, take timestamp
					INSTANCES['latency'].time()
				
				#==================#
				#    INPUT GAIN    #
				#==================#
				
				if SWITCHES['input_gain'] == True:
					
					gain.calculate(data_proc,VARS['input_gain'],IO['period_size'],data_proc)
				
				data_before_filtering = data_proc
				
				if SWITCHES['filtering'] == True:
					
					#========================#
					#    DECOMPOSE SIGNAL    #
					#========================#
					
					if VARS['filtering_method'] == 'FIR':
						outputs = filtering.fir(VARS['h'],data_proc,outputs,c,iptr,IO['period_size'],VARS['ntaps'])
						
					elif VARS['filtering_method'] == 'FFT':
						
						signal_fft = np.fft.rfft(np.append(data_before_filtering[IO['period_size']-VARS['filter_delay']:IO['period_size']],data_proc),VARS['fft_size'])
						
						#========================#
						#    FEEDBACK CONTROL    #
						#========================#
						
						if SWITCHES['feedback_control'] == True:
							signal_fft_magnitude = np.absolute(signal_fft);
							max_index = np.argmax(signal_fft_magnitude[10:signal_fft_magnitude.size-5]) + 10;  #Peak in FFT (ignore very low and high freqs)
							max_value = signal_fft_magnitude[max_index];
							if max_value>np.mean(signal_fft_magnitude) + VARS['feedback_control_threshold']*np.std(signal_fft_magnitude):  # If there's a large peak
								center_freq = max_index*(1.0/(signal_fft_magnitude.size));
								offset = VARS['feedback_control_bandwidth']/(4*IO['fs'])
								h_notch = signal.firwin(VARS['ntaps']-1,[max(0.01,center_freq-offset), min(center_freq+offset,0.99)])
								h_notchfft = np.fft.rfft(h_notch,VARS['fft_size'])
								signal_fft = signal_fft*h_notchfft;
								print(offset)
						
						for i in xrange(0,VARS['bands']):
							o[i] = np.fft.irfft(VARS['hfft'][i]*signal_fft)
							outputs[i] = o[i][VARS['filter_delay']:IO['period_size']+VARS['filter_delay']]
							outputs[i] = outputs[i]*VARS['band%i'%(i+1)]['gain']
					
					for i in xrange(0,VARS['bands']):
						
						#=======================#
						#    NOISE REDUCTION    #
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
						#    COMPRESSION    #
						#===================#
						
						if SWITCHES['band%i'%(i+1)]['comp'] == True:
							alphaA,alphaR = envelope_extraction.time_constants(IO['fs'],VARS['band%i'%(i+1)]['tauA_comp'],VARS['band%i'%(i+1)]['tauR_comp'])
							envelope_extraction.calculate(outputs[i],alphaA,alphaR,IO['period_size'],comp_env0[i],comp_env[i])
							comp_env0[i] = comp_env[i][IO['period_size']-1]
							compression.calculate(outputs[i],IO['period_size'],comp_env[i],VARS['band%i'%(i+1)]['T'],VARS['band%i'%(i+1)]['CR'],VARS['band%i'%(i+1)]['KW'],VARS['band%i'%(i+1)]['MG'],comp_out[i])
							outputs[i] = comp_out[i]
					
					#===============#
					#    SOLOING    #
					#===============#
					
					if True in [SWITCHES['band%i'%(i+1)]['solo'] for i in xrange(0,VARS['bands'])]: # Check if any solos are True
						for i in xrange(0,VARS['bands']): # Loop over bands
							if SWITCHES['band%i'%(i+1)]['solo'] == True: # If solo is true
								data_proc = outputs[i] # Output set to only that band
					else:
						data_proc = sum(outputs)
				
				#======================#
				#    WRITE OUT DATA    #
				#======================#
				
				if SWITCHES['collect_data'] == True:
					input_array[0:IO['period_size']] = data_inp
					output_array[0:IO['period_size']] = data_proc
					input_array[IO['period_size']:] = input_array[0:L-IO['period_size']]
					output_array[IO['period_size']:] = output_array[0:L-IO['period_size']]
					input_array[0:IO['period_size']] = zeros(IO['period_size'])
					output_array[0:IO['period_size']] = zeros(IO['period_size'])
				
				data_proc = array(data_proc,dtype=FORMATS[IO['data_type']]['numpy'])
				
				if SWITCHES['collect_data'] == True: # If data collection is enabled, take second timestamp and write out latency
					INSTANCES['latency'].append()
				
				out.write(data_proc)
				
				last_input = data_inp
				
				if SWITCHES['write_out'] == True:
					with open('input.txt', 'w') as file:
						savetxt(file, input_array, delimiter=',')
					with open('output.txt', 'w') as file:
						savetxt(file, output_array, delimiter=',')
					SWITCHES['write_out'] = False
				
				
			else:
				sleep(wait_time)
			
		else:
			out.write(silence)
	else:
		sleep(0.0001)