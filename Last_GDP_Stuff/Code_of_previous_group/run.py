"""NEW BRANCH???"""


""" FUTURE IMPORTS """
from __future__ import print_function, division
import sys, os

def hearing_aid(offline=False):
	
	#=================#
	#                 #
	#    VARIABLES    #
	#                 #
	#=================#
	
	import ConfigParser
	import json
	from numpy import array
	from time import sleep
	
	cfg = ConfigParser.ConfigParser()
	cfg.read(current_cfg) # Load current configuration file
	
	VARS = {} # Dictionary to hold variables
	FUNC = {} # Dictionary to hold function references
	INSTANCES = {} # Dictionary to hold instance references
	
	def get_defaults(): # Function to grab values from configuration file
		VARS['current_cfg'] = current_cfg
		VARS['f0'] = array(json.loads(cfg.get('filtering','f0')))
		VARS['ntaps'] = int(cfg.getfloat('filtering','ntaps'))
		VARS['bands'] = int(len(VARS['f0']))
		VARS['filtering_method'] = cfg.get('filtering','method')
		VARS['input_gain'] = cfg.getfloat('input_gain','value')
		VARS['feedback_control_threshold'] = cfg.getfloat('feedback_control','threshold')
		VARS['feedback_control_bandwidth'] = cfg.getfloat('feedback_control','bandwidth')
		VARS['data_collection_length'] = cfg.getfloat('data_collection','length')
		for i in xrange(0,VARS['bands']):
			VARS['band'+str(i+1)] = {	'tauA_NR': cfg.getfloat('noise_reduction','attack_time'),
										'tauR_NR': cfg.getfloat('noise_reduction','release_time'),
										'tauA_comp': cfg.getfloat('compression','attack_time'),
										'tauR_comp': cfg.getfloat('compression','release_time'),
										'T': 	cfg.getfloat('compression','threshold'),
										'CR':	cfg.getfloat('compression','compression_ratio'),
										'MG':	cfg.getfloat('compression','makeup_gain'),
										'KW':	cfg.getfloat('compression','knee_width'),
										'gain':	cfg.getfloat('filtering','gain')}
	
	FUNC['get_defaults'] = get_defaults
	get_defaults()
	
	#================#
	#                #
	#    SWITCHES    #
	#                #
	#================#
	
	SWITCHES = {}
	
	SWITCHES['gui'] = cfg.getboolean('startup','gui')
	SWITCHES['debug'] = cfg.getboolean('startup','debug')
	SWITCHES['collect_data'] = cfg.getboolean('startup','collect_data')
	
	l = None
	
	if SWITCHES['gui'] == False:
		l = True
	elif SWITCHES['gui'] == True:
		l = False
	
	SWITCHES['audio'] = l
	SWITCHES['input_gain'] = l
	SWITCHES['filtering'] = l
	SWITCHES['feedback_control'] = l
	
	for i in xrange(0,VARS['bands']):
		SWITCHES['band'+str(i+1)] = {'NR': l, 'comp': l, 'solo': False}
	
	SWITCHES['quit'] = False
	
	
	#===============================#
	#                               #
	#    MISCELLANEOUS FUNCTIONS    #
	#                               #
	#===============================#
	
	def print_debug(x,*args):
		if SWITCHES['debug'] == True:
			print('# ',x)
			for arg in args:
				print('# ',arg)
	
	#======================#
	#                      #
	#    IMPORT MODULES    #
	#                      #
	#======================#
	
	print_debug('IMPORTING MODULES:','')
	
	print_debug('platform')
	import platform
	print_debug('time')
	from time import gmtime, strftime, time, sleep
	print_debug('os')
	import os
	print_debug('threading')
	import threading
	print_debug('numpy')
	import numpy as np
	from numpy import array, zeros, fromstring, int16, int32, float32, float64, log10, round
	print_debug('scipy.signal.firwin')
	from scipy.signal import firwin
	
	print_debug('','IMPORTING SIGNAL PROCESSING BLOCKS:','')
	
	print_debug('gain')
	import gain
	print_debug('filtering')
	import filtering
	print_debug('envelope_extraction')
	import envelope_extraction
	print_debug('compression')
	import compression
	print_debug('noise_reduction')
	import NR
	
	#=================================#
	#                                 #
	#    INPUT & OUTPUT PARAMETERS    #
	#                                 #
	#=================================#
	
	print_debug('Setting audio parameters...')
	
	IO = {}
	
	IO = {
		'period_size': cfg.getint('i/o','period_size'),
		'data_type': cfg.get('i/o','data_type'),
		'channels': cfg.getint('i/o','channels'),
		'card': cfg.get('i/o','card'),
		'fs': cfg.getint('i/o','fs')
		}
	
	FORMATS = {}
	
	from alsaaudio import PCM_FORMAT_S16_LE, PCM_FORMAT_S32_LE, PCM_FORMAT_FLOAT_LE, PCM_FORMAT_FLOAT64_LE
	
	FORMATS = {
			'int16':	{'bytes': 2, 'alsa': PCM_FORMAT_S16_LE,		'numpy': int16},
			'int32':	{'bytes': 4, 'alsa': PCM_FORMAT_S32_LE,		'numpy': int32},
			'float32':	{'bytes': 4, 'alsa': PCM_FORMAT_FLOAT_LE,		'numpy': float32},
			'float64':	{'bytes': 8, 'alsa': PCM_FORMAT_FLOAT64_LE,	'numpy': float64}
			}
	
	frame_size = FORMATS[IO['data_type']]['bytes']*IO['channels'] # Frame size (in bytes) for IO['data_type'] x number of IO['channels']
	
	#===========================#
	#                           #
	#    FILTER COEFFICIENTS    #
	#                           #
	#===========================#
	
	# Calculate lower limits
	VARS['fl'] = round(VARS['f0']/(2**(0.5)))
	
	# Calculate upper limits
	VARS['fu'] = round(VARS['f0']*(2**(0.5)))
	
	# Dummy variables for filter coefficients and FFT of filter coefficients
	VARS['h'] = [None]*VARS['bands']
	VARS['hfft'] = [None]*VARS['bands']
	
	# Calculate optimal FFT size
	VARS['filter_delay'] = VARS['ntaps']*2 # Delay from notch filter + actual filtering
	VARS['fft_size'] = int(2**np.ceil(np.log2(IO['period_size']+VARS['filter_delay']+VARS['ntaps']-1))) # Only when feedback cancellation is turned on?
	print_debug('FFT size set to %s'%(VARS['fft_size']))
	
	# Generate filter coefficients for each band
	for i in xrange(0,VARS['bands']):
		VARS['h'][i] = firwin(VARS['ntaps'],[VARS['fl'][i]/(IO['fs']/2), VARS['fu'][i]/(IO['fs']/2)],pass_zero=False)
		VARS['hfft'][i] = np.fft.rfft(VARS['h'][i],VARS['fft_size'])
	
	#=================#
	#                 #
	#    THREADING    #
	#                 #
	#=================#
	
	import gui
	import audio
	
	t_GUI = threading.Thread(target=gui.GUI,args=(IO,FORMATS,SWITCHES,VARS,FUNC,INSTANCES))
	t_audio = threading.Thread(target=audio.rt,args=(IO,FORMATS,SWITCHES,VARS,FUNC,INSTANCES))
	
	t_GUI.start()
	t_audio.start()

#========================#
#      CONFIG FILES      #
#========================#

import ConfigParser, time, os
from math import ceil

cfg = ConfigParser.ConfigParser()

cfg.add_section('startup')
cfg.set('startup','gui',	'True')
cfg.set('startup','debug',	'True')
cfg.set('startup','collect_data','True')

cfg.add_section('i/o')
cfg.set('i/o','period_size','256')
cfg.set('i/o','data_type',	'float32')
cfg.set('i/o','channels',	'1')
cfg.set('i/o','card',		'plughw:1,0')
cfg.set('i/o','fs',			'12000')

cfg.add_section('input_gain')
cfg.set('input_gain','value','0')

cfg.add_section('noise_reduction')
cfg.set('noise_reduction','attack_time',	'0.005')
cfg.set('noise_reduction','release_time',	'0.02')

cfg.add_section('compression')
cfg.set('compression','attack_time',		'0.005')
cfg.set('compression','release_time',		'0.02')
cfg.set('compression','threshold',			'0')
cfg.set('compression','compression_ratio',	'1')
cfg.set('compression','knee_width',			'10')
cfg.set('compression','makeup_gain',		'0')

cfg.add_section('filtering')
cfg.set('filtering','f0',[250,500,1000,2000,4000])
cfg.set('filtering','ntaps',128)
cfg.set('filtering','gain',1)
cfg.set('filtering','method','FIR')

cfg.add_section('feedback_control')
cfg.set('feedback_control','threshold',5)
cfg.set('feedback_control','bandwidth',0.03)

cfg.add_section('data_collection')
cfg.set('data_collection','length',5)

with open('defaults.ini', 'wb') as cfgfile:
	cfg.write(cfgfile)

current_cfg = 'defaults.ini'

#=============================#
#          MAIN MENU          #
#=============================#

cmd_line = '>> ' # Command line operator

ms = [
	'Guide',
	{
	'Settings':
		[
		'Startup options',
		'Configuration files'
		]},
	'Run (offline)',
	'Run (real-time)'] # Menu structure

# Header
header = 'Welcome to the Raspberry Pi Hearing Aid!\n'

# Main menu
def main_menu():
	os.system('clear')
	print(header)
	print('MAIN MENU\n')
	for i in xrange(0,len(ms)):
		if type(ms[i]) == str:
			print('%i. %s' % (i+1,ms[i]))
		else:
			print('%i. %s' % (i+1,ms[i].keys()[0]))
	print('\n0. Exit\n')
	choice = raw_input(cmd_line)
	exec_menu(choice,main_menu,main_menu)

# Navigator
def exec_menu(choice,current,last):
	os.system('clear')
	ch = choice.lower()
	if ch[-1] == '9':
		print(header)
		last()
	elif ch[-1] == '0':
		sys.exit()
	else:
		try:
			print(header)
			menu_actions[ch]()
		except KeyError:
			print('Invalid selection. Please try again.\n')
			current()

# Documentation
def menu1():
	print('MAIN MENU > %s\n'%(ms[0].upper()))
	print('This is how to use the Raspberry Pi Hearing Aid.')
	print('\n9. Back\n0. Exit\n')
	choice = raw_input(cmd_line)
	exec_menu('1%s'%(choice),menu1,main_menu)

# Settings
def menu2():
	print('MAIN MENU > %s\n'%(ms[1].keys()[0].upper()))
	for i in xrange(0,len(ms[1].values()[0])):
		if type(ms[1].values()[0][i]) == str:
			print('%i. %s' % (i+1,ms[1].values()[0][i]))
		else:
			print('%i. %s' % (i+1,ms[1].values()[0][i].keys()[0]))
	print('\n9. Back\n0. Exit\n')
	choice = raw_input(cmd_line)
	exec_menu('2%s'%(choice),menu2,main_menu)

# Settings > Startup options
def menu21():
	print('MAIN MENU > %s > %s\n'%(ms[1].keys()[0].upper(),ms[1][ms[1].keys()[0]][0].upper()))
	cfg = ConfigParser.ConfigParser()
	cfg.read('defaults.ini')
	print('   GUI................'+str(cfg.get('startup','gui')))
	print('   Debugging..........'+str(cfg.get('startup','debug')))
	print('   Data collection....'+str(cfg.get('startup','collect_data')))
	print('\n1. Toggle GUI')
	print('2. Toggle debugging')
	print('3. Toggle data collection')
	print('\n9. Back\n0. Exit\n')
	choice = raw_input(cmd_line)
	exec_menu('21%s'%(choice),menu21,menu2)

def toggle_gui():
	cfg = ConfigParser.ConfigParser()
	cfg.read('defaults.ini')
	cfg.set('startup','gui',not cfg.getboolean('startup','gui'))
	with open('defaults.ini', 'r+b') as cfgfile:
		cfg.write(cfgfile)
	menu21()
	
def toggle_debug():
	cfg = ConfigParser.ConfigParser()
	cfg.read(current_cfg)
	cfg.set('startup','debug',not cfg.getboolean('startup','debug'))
	with open(current_cfg, 'r+b') as cfgfile:
		cfg.write(cfgfile)
	menu21()

def toggle_collect_data():
	cfg = ConfigParser.ConfigParser()
	cfg.read(current_cfg)
	cfg.set('startup','collect_data',not cfg.getboolean('startup','collect_data'))
	with open(current_cfg, 'r+b') as cfgfile:
		cfg.write(cfgfile)
	menu21()

# Settings > Configuration files
menu22_page = 1
def menu22():
	global current_cfg, menu22_page
	os.system('clear')
	print(header)
	print('MAIN MENU > %s > %s\n'%(ms[1].keys()[0].upper(),ms[1][ms[1].keys()[0]][1].upper()))
	print('The current .ini file is denoted by square brackets.')
	print('To write to a new configuration file, simply enter a desired name.')
	files = []
	files += [each for each in os.listdir(os.getcwd()) if each.endswith('.ini') or each.endswith('.cfg')]
	files.sort()
	menu22_max_pages = int(ceil(len(files)/6))
	menu22_files = [range(0,len(files))[6*i : 6*(i+1)] for i in range(menu22_max_pages)]
	print('\n       Page %i of %i\n'%(menu22_page,menu22_max_pages))
	for i in xrange(0,len(menu22_files[menu22_page-1])):
		if files[menu22_files[menu22_page-1][i]] == current_cfg:
			print('   [%i] %s'%(i+1,files[menu22_files[menu22_page-1][i]].upper()))
		else:
			print('   (%i) %s'%(i+1,files[menu22_files[menu22_page-1][i]]))
	if menu22_page == 1:
		tab = '\n8. Next page'
	elif menu22_page == menu22_max_pages:
		tab ='\n7. Previous page'
	else:
		tab = '\n7. Previous page\n8. Next page'
	print(tab)
	print('\n9. Back\n0. Exit\n')
	choice = raw_input(cmd_line)
	if choice == '7':
		if menu22_page - 1 == 0:
			menu22()
		else:
			menu22_page -= 1
			menu22_files = range(int((menu22_page-1)*(len(files)/menu22_max_pages)),int((menu22_page)*(len(files)/menu22_max_pages)))
			menu22()
	elif choice == '8':
		if menu22_page + 1 > menu22_max_pages:
			menu22()
		else:
			menu22_page += 1
			menu22_files = range(int((menu22_page-1)*(len(files)/menu22_max_pages)),int((menu22_page)*(len(files)/menu22_max_pages)))
			menu22()
	else:
		try:
			ch = int(choice)
			if ch in [0,9]:
				exec_menu('22%s'%(choice),menu22,menu2)
			else:
				try:
					current_cfg = files[ch-1+6*(menu22_page-1)]
					os.system('clear')
					menu22()
				except IndexError:
					menu22()
		except ValueError:
			if '.ini' in choice or '.cfg' in choice:
				new_cfg = choice
			else:
				new_cfg = choice+'.ini'
			confirm = raw_input('%sWould you like to generate \'%s\'? [y/n] '%(cmd_line,new_cfg))
			if confirm.lower() in ['n','no']:
				menu22()
			if confirm.lower() in ['y','yes']:
				with open(new_cfg, 'wb') as cfgfile:
					cfg.write(cfgfile)
					current_cfg = new_cfg
					menu22()
			else:
				print(cmd_line+'That is not a valid selection. Returning...')
				time.sleep(1)
				menu22()

# Offline testing
menu3_page = 1
wav_file = None
notice = ''
def menu3():
	global notice, wav_file, menu3_page
	os.system('clear')
	print(header)
	print('MAIN MENU > %s\n'%(ms[2].upper()))
	print('Please select a .wav file.')
	files = []
	files += [each for each in os.listdir(os.getcwd()) if each.endswith('.wav')]
	files.sort()
	menu3_max_pages = int(ceil(len(files)/6))
	menu3_files = [range(0,len(files))[6*i : 6*(i+1)] for i in range(menu3_max_pages)]
	print('\n       Page %i of %i\n'%(menu3_page,menu3_max_pages))
	for i in xrange(0,len(menu3_files[menu3_page-1])):
		if files[menu3_files[menu3_page-1][i]] == wav_file:
			print('   [%i] %s'%(i+1,files[menu3_files[menu3_page-1][i]].upper()))
		else:
			print('   (%i) %s'%(i+1,files[menu3_files[menu3_page-1][i]]))
	if menu3_max_pages == 1:
		tab = ''
	elif menu3_page == 1:
		tab = '\n8. Next page'
	elif menu3_page == menu3_max_pages:
		tab ='\n7. Previous page'
	else:
		tab = '\n7. Previous page\n8. Next page'
	print(tab)
	print('\n9. Back\n0. Exit\n')
	print(notice)
	choice = raw_input(cmd_line)
	if choice == '7':
		if menu3_page - 1 == 0:
			menu3()
		else:
			menu3_page -= 1
			menu3_files = range(int((menu3_page-1)*(len(files)/menu3_max_pages)),int((menu3_page)*(len(files)/menu3_max_pages)))
			menu3()
	elif choice == '8':
		if menu3_page + 1 > menu3_max_pages:
			menu3()
		else:
			menu3_page += 1
			menu3_files = range(int((menu3_page-1)*(len(files)/menu3_max_pages)),int((menu3_page)*(len(files)/menu3_max_pages)))
			menu3()
	else:
		try:
			ch = int(choice)
			if ch in [0,9]:
				exec_menu('22%s'%(choice),menu3,main_menu)
			else:
				try:
					if files[ch-1+6*(menu3_page-1)] == wav_file:
						os.system('clear')
						hearing_aid(True)
					wav_file = files[ch-1+6*(menu3_page-1)]
					os.system('clear')
					notice = cmd_line+'Please choose again to confirm.'
					menu3()
				except IndexError:
					menu3()
		except ValueError:
			print(cmd_line+'That is not a valid selection. Returning...')
			time.sleep(1)
			menu3()
 
# Exit program
def exit():
	sys.exit()

menu_actions = {
	'main_menu': main_menu,
	'1': menu1,
	'2': menu2,
	'21': menu21,
	'211': toggle_gui,
	'212': toggle_debug,
	'213': toggle_collect_data,
	'22': menu22,
	'3': menu3,
	'4': hearing_aid,
	'0': exit,
}

if __name__ == '__main__': 
	main_menu()
