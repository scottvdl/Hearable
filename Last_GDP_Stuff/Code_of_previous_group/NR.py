from scipy import weave

def wiener(N,env,x,y):
	c_code = """
	//N = chunk size
	//env = envelope
	//x = raw data
	//y = outputted data
	
	
	// Declare variables 
	double SNR;
	double largest;
	double smallest;
	double W;
	double WdB;
	
	largest = env[0]; //Set first value of envelope to largest
	smallest = env[0]; //Set first value of envelope to smallest
	
	// Use for loop to find envelope min and max
	for (int i=1; i<N ; i++) {
		
		if (env[i] > largest) {
			largest = env[i];
		}
		
		if (env[i] < smallest) {
			smallest = env[i];
		}
	}
	
	// Estimate SNR 
	SNR = 10*log10(largest/smallest);
	
	
	// Wiener, calculates gain reduction
	W = ( SNR ) / ( SNR + 1.0 ) ;
	
	// Log weiner gain
	WdB = 20*log10(W);
	
	// Apply change of gain
	for (int i=0; i<N ; i++) {
		y[i] = x[i] * pow( (double) 10.0, (WdB/20.0));
	}
	return_val = 0;
	"""
	return weave.inline(c_code,['N','env','x','y'],compiler='gcc')