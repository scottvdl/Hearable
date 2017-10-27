from scipy import weave 

def calculate(x,gdB,N,y):
	c_code = """
	
	// Main Code
	for (int i=0; i<N ; i++) {
		y[i] = x[i] * pow( (double) 10.0, (gdB/20.0));
	}
	
	return_val =  0;
	"""
	return weave.inline(c_code,['x','gdB','N','y'],compiler='gcc')
	