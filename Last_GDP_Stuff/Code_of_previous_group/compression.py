from scipy import weave
from numpy import exp

def calculate(x,N,env,T,CR,KW,MG,y):
	c_code = """
	
	int i = 0;
	double ydB;
	
	while (i < N) {
		
		double xdB = 20*log10(fabs(x[i]));
		double envdB = 20*log10(fabs(env[i]));
		
		if ( ( 2 * ( envdB - T ) ) < - KW ) {
			ydB = xdB;
		}
		else if ( ( 2 * abs ( envdB - T ) ) <= KW ) {
			ydB = xdB+(1/CR-1)*pow((xdB-T+(KW/2)),2)/(2*KW);
		}
		else if ( ( 2 * ( envdB - T ) ) > KW ) {
			ydB = T+((xdB-T)/CR);
		}
		ydB = ydB + MG;
		y[i] = pow(10,ydB/20);
		
		if ( x[i] < 0 ) {
			y[i] = -y[i];
		}
		
		i++;
	}
	return_val = 0;
	"""
	return weave.inline(c_code,['x','N','env','T','CR','KW','MG','y'],compiler='gcc')