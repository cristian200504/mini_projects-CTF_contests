import pickle, math
b=pickle.load(open('/tmp/lll_K4.pkl','rb'))
print(len(b),len(b[0]))
for i in [0,255,511,767,768,900,1023]:
    print(i,math.sqrt(sum(x*x for x in b[i])),sum(x!=0 for x in b[i]))
# Load only definitions, without starting another lattice job.
ns={ '__file__': 'solve.py' }
exec(open('solve.py').read().split('order = list(range(10))')[0],ns)
inv=ns['ring_inv'](ns['S_all'][0])
assert ns['rmul'](inv,ns['S_all'][0])==[1]+[0]*255
print('Polynomial inverse verified')
