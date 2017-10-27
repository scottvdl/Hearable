from scipy import weave
from numpy import zeros,array,add,size,reshape,sum,append,fft,ceil,log2,append

""" Ring buffer FIR """
def f(h,inp,output,c,iptr,N,ntaps):
	c_code = """
			int i, k, index;
			
			for (k = 0; k < N; k++) {
				double out = 0;
				c[iptr] = inp[k];
				index = iptr;
				for (i = 0; i < ntaps; i++) {
					if (index < 0) index = N - 1;
					out += c[(index)]*h[i];
					index = index - 1;
				}
				iptr = (iptr + 1) % N;
				output[k] = out;
			}
			return_val = 0;
			"""
	return weave.inline(c_code,['h','inp','output','c','iptr','N','ntaps'],compiler='gcc')

def fir(h,data_proc,outputs,c,iptr,N,ntaps):
	for i in xrange(0,len(outputs)):
		f(h[i],data_proc,outputs[i],c[i],iptr,N,ntaps)
	return outputs