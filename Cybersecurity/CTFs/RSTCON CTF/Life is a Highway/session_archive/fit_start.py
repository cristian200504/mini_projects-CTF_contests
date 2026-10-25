import xml.etree.ElementTree as E,numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import differential_evolution,minimize
D=np.load('fitted.npz');t=D['t'];lat0,lon0=D['ll'][0];my=111111.;mx=my*np.cos(np.deg2rad(lat0));root=E.parse('start_map.osm').getroot();nodes={int(n.get('id')):((float(n.get('lon'))-lon0)*mx,(float(n.get('lat'))-lat0)*my) for n in root.findall('node')};points=[];fast=[];rt=[]
for w in root.findall('way'):
 tag={v.get('k'):v.get('v') for v in w.findall('tag')}
 if tag.get('highway') not in ('service','unclassified','residential','tertiary','secondary','primary','trunk','motorway','primary_link','secondary_link','trunk_link','motorway_link'):continue
 p=np.array([nodes[int(n.get('ref'))] for n in w.findall('nd')]);P=[]
 for a,b in zip(p[:-1],p[1:]):P.extend(np.linspace(a,b,max(2,int(np.linalg.norm(b-a)/2))))
 points.extend(P)
 if tag.get('highway') in ('secondary','primary','trunk','motorway','primary_link','secondary_link','trunk_link','motorway_link'):fast.extend(P)
 if 'VA 7' in tag.get('ref','') and p[-1,0]>p[0,0]:rt.extend(P)
T=cKDTree(points);F=cKDTree(fast);R=cKDTree(rt)
sel=(t>22)&(t<200);P=np.column_stack([(D['ll'][:,1]-lon0)*mx,(D['ll'][:,0]-lat0)*my])[sel][::5];ts=t[sel][::5];mask1=ts<85;mask2=(ts>=85)&(ts<140);mask3=ts>=140

def transform(params,p=P):
 x,y,theta=params;a=np.deg2rad(theta);rot=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]]);return p@rot.T+np.array([x,y])
def loss(params):
 q=transform(params);d=np.r_[T.query(q[mask1])[0],F.query(q[mask2])[0],R.query(q[mask3])[0]];return np.mean(d**2)
if __name__=='__main__':
 fit=differential_evolution(loss,[(-800,800),(-800,800),(-30,30)],tol=1e-6,popsize=12,maxiter=180,seed=4,polish=True)
 print('fit',fit.x,'rms',np.sqrt(fit.fun),'start latlon',lat0+fit.x[1]/my,lon0+fit.x[0]/mx,flush=True);np.savez_compressed('start_fitted.npz',params=fit.x,start=np.array([lat0+fit.x[1]/my,lon0+fit.x[0]/mx]),P=transform(fit.x),t=ts,origin=np.array([lat0,lon0]))
