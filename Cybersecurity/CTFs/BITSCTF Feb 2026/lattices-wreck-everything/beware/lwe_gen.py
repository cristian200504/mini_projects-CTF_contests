from random import randrange
import numpy as np
import json
from ntrugen import ntru_gen
from ntt import div_zq
from ntru_gen import NTRUKeyGenerator

def generateLWEInstance(scheme):
  implementedSchemes = [
    "Kyber512", "Kyber768", "Kyber1024",
    "Dilithium2", "Dilithium3", "Dilithium5",
    "Falcon2", "Falcon4", "Falcon8", "Falcon16", "Falcon32", "Falcon64", "Falcon128", "Falcon256", "Falcon512", "Falcon1024",
    "NTRU-HPS-509", "NTRU-HPS-677", "NTRU-HPS-821", "NTRU-HRSS"
  ]

  if scheme not in implementedSchemes:
    raise NotImplementedError( "Scheme " + scheme + " is not supported." )

  if scheme.startswith("Kyber"):
    variant = int(scheme[5:])
    A,s,e,q = kyberGen(variant)
  elif scheme.startswith("Dilithium"):
    variant = int(scheme[9:])
    A,s,e,q = dilithiumGen(variant)
  elif scheme.startswith("Falcon"):
    variant = int(scheme[6:])
    A,s,e,q = falconGen(variant)
  elif scheme.startswith("NTRU"):
    scheme = scheme[5:]
    A,s,e,q = ntruGen(scheme)

  b = (s.dot(A) + e) % q

  return A,b,q,s,e


def loadLWEInstanceFromFile( fileName = None ):
  with open(fileName) as f:
      
      data = json.load(f)
      q = int(data["q"])
      A = np.array(data["A"])
      b = np.array(data["b"])
      
      if not( "s" in data and "e" in data ):
        return A,b,q
      
      else:
        s = np.array(data["s"])
        e = np.array(data["e"])
        return A,b,q,s,e
  
def generateToyInstance(n,m,q,eta):
  A,s,e = binomialLWEGen(n,m,q,eta)
  b = (s.dot(A) + e) % q
  
  return A,b,q,s,e

def binomial_dist(eta):
  s = 0
  for i in range(eta):
    s += randrange(2)
  return s
def binomial_vec(n, eta):
  v = np.array([0]*n)
  for i in range(n):
    v[i] = binomial_dist(2*eta) - eta
  return v
def uniform_vec(n, a, b):
  return np.array([randrange(a,b) for _ in range(n)])
def rotMatrix(poly, cyclotomic=False):
  n = len(poly)
  A = np.array( [[0]*n for _ in range(n)] )
  
  for i in range(n):
    for j in range(n):
      c = 1
      if cyclotomic and j < i:
        c = -1

      A[i][j] = c * poly[(j-i)%n]
      
  return A
def module( polys, rows, cols ):
  if rows*cols != len(polys):
    raise ValueError("len(polys) has to equal rows*cols.")
  
  n = len(polys[0])
  for poly in polys:
    if len(poly) != n:
      raise ValueError("polys must not contain polynomials of varying degrees.")
  
  blocks = []
  
  for i in range(rows):
    row = []
    for j in range(cols):
      row.append( rotMatrix(polys[i*cols+j], cyclotomic=True) )
    blocks.append(row)
  return np.block( blocks )
def binomialLWEGen(n,m,q,eta):
  A = np.array( [[0]*m for _ in range(n)] )
  for i in range(n):
    for j in range(m):
      A[i][j] = randrange(q)
  s = binomial_vec(n, eta)
  e = binomial_vec(m, eta)
  return A,s,e
  
def kyberGen(variant):
  if variant not in [512,768,1024]:
    raise NotImplementedError("kyberGen(variant) supports only variant = 512, 768, 1024, but variant = %d was given." % variant)
  
  n = 256
  q = 3329
  k = variant//n
  
  if k == 2:
    eta = 3
  else:
    eta = 2
  
  s = binomial_vec(variant, eta)
  e = binomial_vec(variant, eta)
  
  polys = []
  for i in range(k*k):
    polys.append( uniform_vec(n,0,q) )
  
  A = module(polys, k, k)
  
  return A,s,e,q
def dilithiumGen(variant):
  if variant not in [2,3,5]:
    raise NotImplementedError("dilithiumGen(variant) supports only variant = 2, 3, 5, but variant = %d was given." % variant)
  
  n = 256
  q = 8380417
  
  if variant == 2:
    k = 4
    l = 4
    eta = 2
  elif variant == 3:
    k = 6
    l = 5
    eta = 4
  else:
    k = 8
    l = 7
    eta = 2
  
  s = uniform_vec(n*l,-eta,eta+1)
  e = uniform_vec(n*k,-eta,eta+1)
  
  polys = []
  for i in range(k*l):
    polys.append( uniform_vec(n,0,q) )
  
  A = module(polys, l, k)
  
  return A,s,e,q
def falconGen(n):
  if n not in [ 2**i for i in range(1,11) ]:
    raise NotImplementedError("falconGen(n) supports only n = 2, 4, ..., 1024 but n = %d was given." % n)
  
  q = 12289
  
  f, g, F, G = ntru_gen(n)
  h = div_zq(g, f)
  
  A = rotMatrix(h, cyclotomic=True)
  s = np.array(f)
  e = -np.array(g)
  
  return A,s,e,q
def ntruGen(variant):
  if variant not in ["HPS-509", "HPS-677", "HPS-821", "HRSS"]:
    raise NotImplementedError("ntruGen(variant) supports only variant = HPS-509, HPS-677, HPS-821, HRSS but " + variant + " was given.")
    
  if variant == "HRSS":
    useHRSS = True
    n = 701
    q = 8192
  else:
    useHRSS = False
    n = int(variant[4:])
    if n == 821:
      q = 4096
    else:
      q = 2048
    
  generator = NTRUKeyGenerator(useHRSS, n, q)
  seed = generator.newSeed()
  f,g,h = generator.getKey(seed)
  
  A = rotMatrix(h)
  s = np.array(f)  
  e = -np.array(g)
  
  return A,s,e,q