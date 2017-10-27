def GUI(IO,FORMATS,SWITCHES,VARS,FUNC,INSTANCES):
	
	import Tkinter as Tk
	import sys
	
	root = Tk.Tk() # Create Tkinter object
	
	#=====================#
	#                     #
	#    GUI VARIABLES    #
	#                     #
	#=====================#
	
	freqs = [] # Frequency labels
	for f in VARS['f0']:
		if f < 1000:
			freqs.append('%i Hz'%(f))
		else:
			freqs.append('%i kHz'%(f/1000))
	
	#=================#
	#                 #
	#    PROTOCOLS    #
	#                 #
	#=================#
	
	def on_closing():
		SWITCHES['quit'] = True
		root.destroy()
		sys.exit()
	
	root.protocol("WM_DELETE_WINDOW", on_closing)
	
	#===============#
	#               #
	#    CLASSES    #
	#               #
	#===============#
	
	class Slider():
		
		def __init__(self,master,orient,min,max,res,label,band,var,r,c,cspan=1,w=None):
			self.master = master
			self.orient = orient
			self.min = min
			self.max = max
			self.res = res
			self.label = label
			self.band = band
			self.var = var
			self.r = r
			self.c = c
			self.cspan = cspan
			self.w = w
			slider = Tk.Scale(self.master,orient=self.orient,from_=self.min, to=self.max, label=self.label, command=self.get, resolution=self.res,length=w[1])
			self.slider = slider
			self.slider.grid(row=self.r,column=self.c,columnspan=self.cspan)
			if self.band == None:
				self.slider.set(VARS[self.var])
			else:
				self.slider.set(VARS[self.band][self.var])
		
		def get(self,val):
			if self.band == None:
				VARS[self.var] = float(val)
			else:
				VARS[self.band][self.var] = float(val)
		
		def reset(self):
			self.slider.set(VARS[self.band][self.var])
	
	class ToggleButton():
	
		def __init__(self,master,text,band,var,r,c,cspan=1,w=None,ME=False):
			self.master = master
			self.text = text
			self.band = band
			self.var = var
			self.r = r
			self.c = c
			self.cspan = cspan
			self.w = w
			self.ME = ME
			self.btn = Tk.Button(self.master,text=self.text,command=self.toggle,width=w[0])
			self.btn.grid(row=self.r,column=self.c,columnspan=self.cspan)
			
		def toggle(self):
			reliefs = ['raised','sunken']
			if self.ME == False:
				if self.band == None:
					SWITCHES[self.var] = not SWITCHES[self.var]
					self.btn.config(relief=reliefs[SWITCHES[self.var]])
				else:
					SWITCHES[self.band][self.var] = not SWITCHES[self.band][self.var]
					self.btn.config(relief=reliefs[SWITCHES[self.band][self.var]])
			elif self.ME == True:
				if self.band == None:
					SWITCHES[self.var] = not SWITCHES[self.var]
					self.btn.config(relief=reliefs[SWITCHES[self.var]])
				else:
					for i in filter(lambda a: a != int(self.band[-1]), range(1,VARS['bands']+1)):
						SWITCHES['band'+str(i)][self.var] = False
						organiser['%s_%i'%(self.var,i)].btn.config(relief='raised')
					SWITCHES[self.band][self.var] = not SWITCHES[self.band][self.var]
					self.btn.config(relief=reliefs[SWITCHES[self.band][self.var]])
	
	#==========================#
	#                          #
	#    CALLBACK FUNCTIONS    #
	#                          #
	#==========================#
	
	def reset():
		FUNC['get_defaults']()
		for i in xrange(0,len(freqs)):
			organiser['slider_gain_'+str(i)].reset()
			organiser['slider_NR_tauA_'+str(i)].reset()
			organiser['slider_NR_tauR_'+str(i)].reset()
			organiser['slider_comp_tauA_'+str(i)].reset()
			organiser['slider_comp_tauR_'+str(i)].reset()
			organiser['slider_T_'+str(i)].reset()
			organiser['slider_CR_'+str(i)].reset()
			organiser['slider_KW_'+str(i)].reset()
			organiser['slider_MG_'+str(i)].reset()
		return
	
	def save_data():
		SWITCHES['write_out'] = True
		return
	
	#======================#
	#                      #
	#    INITIALISE GUI    #
	#                      #
	#======================#
	
	max_cols = 4
	p_big = 0
	p_small = 0
	mid = int(round(max_cols/2)-1)
	pad_f = 5
	w = [15,120]
	
	#=====================#
	#                     #
	#    MAIN CONTROLS    #
	#                     #
	#=====================#
	
	if False:
		
		current_row = 0
		current_col = 0
		
		""" MODULES FRAME """
		f_main = Tk.LabelFrame(root,text='Modules',labelanchor='n',padx=pad_f,pady=pad_f)
		f_main.grid(row=current_row,column=current_col,padx=pad_f,pady=pad_f)
		
		# Audio toggle button
		toggle_audio = ToggleButton(f_main,'Audio',None,'audio',current_row,current_col, w=w)
		current_row += 1
		
		# Input gain frame
		f_input_gain = Tk.LabelFrame(f_main,text='Input gain',labelanchor='n',padx=pad_f,pady=pad_f)
		f_input_gain.grid(row=current_row,column=current_col,padx=pad_f,pady=pad_f)
		# Input gain toggle button
		toggle_input_gain = ToggleButton(f_input_gain,'Input gain',None,'input_gain',current_row,current_col,w=w)
		current_row += 1
		# Input gain slider
		slider_input_gain = Slider(f_input_gain,'horizontal',-100,100,0.1,None,None,'input_gain',current_row,current_col,w=w)
		current_row += 1
		
		# Filter toggle
		toggle_filtering = ToggleButton(f_main,'Filtering',None,'filtering',current_row,current_col,w=w)
		current_row += 1
		
		# Feedback control frame
		f_feedback = Tk.LabelFrame(f_main,text='Feedback reduction',labelanchor='n',padx=pad_f,pady=pad_f)
		f_feedback.grid(row=current_row,column=current_col,padx=pad_f,pady=pad_f)
		# Feedback reduction toggle button
		toggle_feedback = ToggleButton(f_feedback,'Feedback control',None,'feedback_control',current_row,current_col,w=w)
		current_row += 1
		# Feedback reduction threshold slider
		slider_feedback_threshold = Slider(f_feedback,'horizontal',1,10,0.1,'Threshold',None,'feedback_control_threshold',current_row,current_col,w=w)
		current_row += 1
		# Feedback reduction bandwidth slider
		slider_feedback_bandwidth = Slider(f_feedback,'horizontal',1,120,0.1,'Bandwidth',None,'feedback_control_bandwidth',current_row,current_col,w=w)
		current_row += 1
		
		""" FUNCTIONS FRAME """
		f_func = Tk.LabelFrame(root,text='Functions',labelanchor='n',padx=pad_f,pady=pad_f)
		f_func.grid(row=current_row,column=current_col,padx=pad_f,pady=pad_f)
		
		# Reset variables button
		btn_reset = Tk.Button(f_func, text='Reset variables', command=reset, width=w[0])
		btn_reset.grid(row=current_row,column=current_col)
		current_row += 1
		
		# Save current state button
		btn_save_cfg = Tk.Button(f_func, text='Save config', command=reset, width=w[0])
		btn_save_cfg.grid(row=current_row,column=current_col)
		current_row += 1
		
		# Countdown button
		btn_countdown = Tk.Button(f_func, text='Countdown', command=INSTANCES['countdown'].go, width=w[0])
		btn_countdown.grid(row=current_row,column=current_col)
		current_row += 1
		
		""" DATA COLLECTION FRAME """
		if SWITCHES['collect_data'] == True:
			f_data = Tk.LabelFrame(root,text='Data collection',labelanchor='n',padx=pad_f,pady=pad_f)
			f_data.grid(row=current_row,column=current_col,padx=pad_f,pady=pad_f)
			btn_save_latency = Tk.Button(f_data, text='Export latency', command=INSTANCES['latency'].export,width=w[0])
			btn_save_latency.grid(row=current_row,column=current_col)
			current_row += 1
			btn_save_data = Tk.Button(f_data, text='Export data', command=save_data, width=w[0])
			btn_save_data.grid(row=current_row,column=current_col)
			current_row += 1
			data_length_text = '(Last %s s of data retained)'%(str(VARS['data_collection_length']))
			data_length = Tk.Label(f_data,text=data_length_text)
			data_length.grid(row=current_row,column=current_col)
			current_row += 1
		
		""" INFO FRAME """
		f_info = Tk.LabelFrame(root,text='I/O',labelanchor='n',padx=pad_f,pady=pad_f)
		f_info.grid(row=current_row,column=current_col,padx=pad_f,pady=pad_f)
		
		if IO['fs'] > 1000:
			fs_text = 'Sampling frequency: %i kHz'%(IO['fs']/1000)
		else:
			fs_text = 'Sampling frequency: %i kHz'%(IO['fs'])
		
		fs = Tk.Label(f_info,text=fs_text)
		fs.grid(row=current_row,column=current_col)
		current_row += 1
		
		buffer_length = Tk.Label(f_info,text='Buffer length: %i samples'%(IO['period_size']))
		buffer_length.grid(row=current_row,column=current_col)
		current_row += 1
		
		max_latency = Tk.Label(f_info,text='Software latency: %i ms'%(IO['period_size']*1000/IO['fs']))
		max_latency.grid(row=current_row,column=current_col)
		current_row += 1
		
		config = Tk.Label(f_info,text='Current config: \'%s\''%(VARS['current_cfg']))
		config.grid(row=current_row,column=current_col)
		
		""" FILTERING WINDOW """
		
		tl_filtering = Tk.Toplevel()
		
		current_row = 0
		current_col = 0
		
		f_filtering = Tk.LabelFrame(tl_filtering,text='Filtering')
		f_filtering.grid(row=current_row,column=current_col,columnspan=5,padx=pad_f,pady=pad_f)
		current_row += 1
		
		organiser = dict()
		
		for i in xrange(0,len(freqs)):
			organiser['f_freq_'+str(i)] = Tk.LabelFrame(f_filtering,text=freqs[i])
			organiser['f_freq_'+str(i)].grid(row=i,column=current_col,padx=pad_f,pady=pad_f)
		
		current_row += 1
		
		for i in xrange(0,len(freqs)):
			
			organiser['solo_'+str(i+1)] = ToggleButton(organiser['f_freq_'+str(i)],'Solo','band'+str(i+1),'solo',i,current_col,w=w,ME=True)
			organiser['slider_gain_'+str(i)] = Slider(organiser['f_freq_'+str(i)],'horizontal',0,3,0.1,'Gain','band'+str(i+1),'gain',i+1,current_col,w=w)
			current_col += 1
			organiser['btn_toggle_NR_'+str(i)] = ToggleButton(organiser['f_freq_'+str(i)],'Noise reduction','band'+str(i+1),'NR',i,current_col,cspan=2,w=w)
			organiser['slider_NR_tauA_'+str(i)] = Slider(organiser['f_freq_'+str(i)],'horizontal',0.001,0.5,0.001,'tauA','band'+str(i+1),'tauA_NR',i+1,current_col,w=w)
			current_col += 1
			organiser['slider_NR_tauR_'+str(i)] = Slider(organiser['f_freq_'+str(i)],'horizontal',0.001,2,0.001,'tauR','band'+str(i+1),'tauR_NR',i+1,current_col,w=w)
			current_col += 1
			organiser['btn_toggle_comp_'+str(i)] = ToggleButton(organiser['f_freq_'+str(i)],'Compression','band'+str(i+1),'comp',i,current_col,cspan=6,w=w)
			organiser['slider_comp_tauA_'+str(i)] = Slider(organiser['f_freq_'+str(i)],'horizontal',0.001,0.5,0.001,'tauA','band'+str(i+1),'tauA_comp',i+1,current_col,w=w)
			current_col += 1
			organiser['slider_comp_tauR_'+str(i)] = Slider(organiser['f_freq_'+str(i)],'horizontal',0.001,2,0.001,'tauR','band'+str(i+1),'tauR_comp',i+1,current_col,w=w)
			current_col += 1
			organiser['slider_T_'+str(i)] = Slider(organiser['f_freq_'+str(i)],'horizontal',-100,100,0.1,'T','band'+str(i+1),'T',i+1,current_col,w=w)
			current_col += 1
			organiser['slider_CR_'+str(i)] = Slider(organiser['f_freq_'+str(i)],'horizontal',1,40,0.1,'CR','band'+str(i+1),'CR',i+1,current_col,w=w)
			current_col += 1
			organiser['slider_MG_'+str(i)] = Slider(organiser['f_freq_'+str(i)],'horizontal',0,30,0.1,'MG','band'+str(i+1),'MG',i+1,current_col,w=w)
			current_col += 1
			organiser['slider_KW_'+str(i)] = Slider(organiser['f_freq_'+str(i)],'horizontal',0,40,0.1,'KW','band'+str(i+1),'KW',i+1,current_col,w=w)
	
	else:
		
		tabs =	[
				'Playback',
				'Compression',
				'Debug'
				]
		
		ORGANISER = {}
		
		for i in xrange(0,len(tabs)):
			ORGANISER['tab%i'%(i)] = {'label',tabs(i)}
		
		print(ORGANISER)
		
	
	root.mainloop()