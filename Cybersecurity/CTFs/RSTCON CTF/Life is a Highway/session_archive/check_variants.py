import fit_analysis as f,numpy as np
from scipy.integrate import cumulative_trapezoid as cint
from scipy.spatial import cKDTree
from scipy.optimize import minimize
D=np.load('fitted.npz');base=D['params'];time=(f.tr-f.tr.mean())/f.tr[-1];B=cint(time*f.moving,f.tr,initial=0);B-=B[f.ref]

def trace(params,gain=1,drift=False):
 bias,heading,scale=params[:3];h=gain*f.Y-np.deg2rad(bias)*f.M+np.deg2rad(heading)
 if drift:h-=np.deg2rad(params[3])*B
 x=cint(f.v*scale*np.cos(h),f.tr,initial=0);y=cint(f.v*scale*np.sin(h),f.tr,initial=0);return np.column_stack([x-x[-1],y-y[-1]])
def loss(p,gain,drift):
 xy=trace(p,gain,drift);d=cKDTree(xy[f.mask]).query(f.P)[0];return np.mean(d*d)
for gain,drift in [(1.0,False),(.25/.244,False),(1.0,True)]:
 ini=list(base)+([0] if drift else []);bounds=[(.04,.14),(155,190),(.97,1.03)]+([(-.15,.15)] if drift else []);res=minimize(loss,ini,args=(gain,drift),bounds=bounds,method='Nelder-Mead',options={'maxiter':1500,'xatol':1e-7,'fatol':1e-4});xy=trace(res.x,gain,drift);lat=f.lat0+xy[0,1]/f.my;lon=f.lon0+xy[0,0]/f.mx;print('gain',gain,'linear drift',drift,'rms',res.fun**.5,'parameters',res.x,'start',lat,lon,flush=True)
 np.savez_compressed('variant_'+str(gain)+'_'+str(drift)+'.npz',params=res.x,xy=xy,ll=np.column_stack([f.lat0+xy[:,1]/f.my,f.lon0+xy[:,0]/f.mx]),t=f.tr)
