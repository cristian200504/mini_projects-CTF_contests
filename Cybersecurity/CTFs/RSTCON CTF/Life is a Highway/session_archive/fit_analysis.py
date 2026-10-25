import numpy as np,json
from scipy.integrate import cumulative_trapezoid as cint
from scipy.spatial import cKDTree
from scipy.optimize import differential_evolution,minimize
from pathlib import Path
D=np.load('can_signals.npz');raw=D['024'];ts=raw[:,0];t=np.arange(ts[0],ts[-1],.15);tr=t-t[0]
yr=np.interp(t,ts,((raw[:,1].astype(int)&3)*256+raw[:,2]-512)*.244)
v=D['0B4'];v=np.interp(t,v[:,0],(v[:,6]*256+v[:,7])*.01/3.6);moving=v>.1
g=np.load('gears.npz');gear=g['gear'][np.clip(np.searchsorted(g['t'],t,side='right')-1,0,len(g['t'])-1)];v[gear==16]*=-1
Y=cint(np.deg2rad(yr*moving),tr,initial=0);M=cint(moving.astype(float),tr,initial=0);ref=abs(tr-1735).argmin();Y-=Y[ref];M-=M[ref]
lat0,lon0=38.9166896,-77.2210292;my=111111.;mx=my*np.cos(np.deg2rad(lat0));roads=json.load(open('rt7_geometry.json'));points=[]
for road in roads.values():
 ll=np.array(road['coords']);p=np.column_stack([(ll[:,1]-lon0)*mx,(ll[:,0]-lat0)*my]);
 if p[-1,0]<p[0,0]:continue
 for a,b in zip(p[:-1],p[1:]):points.extend(np.linspace(a,b,max(2,int(np.linalg.norm(b-a)/15))))
P=np.array(points);P=np.unique(np.rint(P/5)*5,axis=0);mask=(tr>145)&(tr<1545)
# Keep road reference points only between 1 km and 20 km from endpoint.
P=P[(np.linalg.norm(P,axis=1)<20000)&(np.linalg.norm(P,axis=1)>800)]

def trace(params):
 bias,heading,scale=params;h=Y-np.deg2rad(bias)*M+np.deg2rad(heading);x=cint(v*scale*np.cos(h),tr,initial=0);y=cint(v*scale*np.sin(h),tr,initial=0);return np.column_stack([x-x[-1],y-y[-1]])
def loss(params):
 p=trace(params);tree=cKDTree(p[mask]);d=tree.query(P)[0];return np.mean(np.minimum(d,3000)**2)
if __name__=='__main__':
 print('Reference points',P.shape,flush=True)
 fit=differential_evolution(loss,[(.04,.14),(160,185),(.98,1.02)],tol=.00001,popsize=9,maxiter=100,seed=2,polish=True,workers=1)
 print('fit',fit.x,'rms',np.sqrt(fit.fun),fit.message,flush=True)
 xy=trace(fit.x);ll=np.column_stack([lat0+xy[:,1]/my,lon0+xy[:,0]/mx]);print('start',ll[0],flush=True)
 for tm in range(0,1800,120):
  i=abs(tr-tm).argmin();print(tm,ll[i],flush=True)
 np.savez_compressed('fitted.npz',params=fit.x,t=tr,xy=xy,ll=ll,P=P)
