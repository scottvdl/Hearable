from scipy import weave
from numpy import exp

def time_constants(fs,tauA,tauR):
	alphaA = exp(-1/(tauA*fs))
	alphaR = exp(-1/(tauR*fs))
	return alphaA,alphaR

def calculate(x,alphaA,alphaR,N,env0,env):
	c_code = """
	
	int i = 0;
	double alpha;
	double x_abs;
	double y0;
	
	while (i <= N) {
	
		x_abs = fabs(x[i]);
		
		if (i == 0) {
			y0 = env0;
		}
		else {
			y0 = env[i-1];
		}
		
		if ( x_abs > y0 ) {
			alpha = alphaA;
		}
		else {
			alpha = alphaR;
		}
		
		env[i] = alpha * y0 + (1 - alpha) * x_abs;
		
		i++;
	}
	
	env0 = env[N-1];
	
	return_val = env0;
	
	"""
	env0 = weave.inline(c_code,['N','x','alphaA','alphaR','env0','env'],compiler='gcc')
	return env,env0