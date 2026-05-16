# coding: utf-8

from random import SystemRandom
from sympy import *
import math
import numpy as np
import sys
class NTRUKeyGenerator:
  phi_1 = [-1,1]
  x = symbols('x')
  def __init__(self, HRSS, n, q=0):
    self.HRSS = HRSS
    self.n = n
    self.q = q
    
    self.cache = {}
    
    self.phi_n = [1]*n

    self.sample_iid_bits = 8*(n-1)
    self.sample_fixed_type_bits = 30*(n-1)

    if HRSS:
      self.q = 2**math.ceil(7/2+math.log2(n))
      self.sample_key_bits = 2*self.sample_iid_bits
    else:
      self.sample_key_bits = self.sample_iid_bits + self.sample_fixed_type_bits

    self.logq = int(math.log2(self.q))
  def randomBitArray(self, s):
    random = SystemRandom()
    return [ ( random.randrange(2) ) for i in range(s) ]
  def newSeed(self):
    return self.randomBitArray(self.sample_key_bits)
  def polyToSympy(self, poly):
    return Poly( poly[::-1], self.x )
  def sympyToPoly(self, symPoly):
    try:
      return symPoly.all_coeffs()[::-1]
    except:
      return [symPoly]
  def polyCoeffMod(self, poly,m):
    for i in range(len(poly)):
      poly[i] = poly[i] % m
      if m!=2 and poly[i] >= m/2:
        poly[i] -= m
    return poly
  def sympyPolyCoeffMod2(self, symPoly):
    return self.polyToSympy( self.polyCoeffMod( self.sympyToPoly(symPoly), 2 ) )
  def polyMod(self, poly1, m, poly2):
    poly1Sym = self.polyToSympy(poly1)
    poly2Sym = self.polyToSympy(poly2)

    q,r = div(poly1Sym,poly2Sym)

    poly1Sym = r
    poly1 = self.sympyToPoly(poly1Sym)

    poly1 = self.polyCoeffMod(poly1,m)

    return poly1
  def polynomialEEA_mod2(self, f_1, f_2):
    zeroPoly = self.polyToSympy([0])
    onePoly = self.polyToSympy([1])

    if f_1 == zeroPoly:
        f_2 = self.sympyPolyCoeffMod2(f_2)
        return (f_2, zeroPoly, onePoly)
    else:
        q,r = div( f_2, f_1 )

        q = self.sympyPolyCoeffMod2(q)
        r = self.sympyPolyCoeffMod2(r)

        g, s, t = self.polynomialEEA_mod2(r, f_1)
        return (self.sympyPolyCoeffMod2(g), self.sympyPolyCoeffMod2(t-q*s), self.sympyPolyCoeffMod2(s))
  def S2_(self, poly):
    return self.polyMod(poly,2,self.phi_n)
  def S3_(self, poly):
    return self.polyMod(poly,3,self.phi_n)
  def Sq_(self, poly):
    return self.polyMod(poly,self.q,self.phi_n)
  def S2_inverse(self, poly):
    g,s,t = self.polynomialEEA_mod2( self.polyToSympy(poly), self.polyToSympy(self.phi_n) )
    if g != self.polyToSympy([1]):
      raise ZeroDivisionError
    return self.sympyToPoly(s)
  def Sq_inverse(self, a):
    v_0 = self.S2_inverse(a)
    t = 1
    while t < self.logq:
      sympA = self.polyToSympy(a)
      sympV = self.polyToSympy(v_0)
      sympV = sympV * (2 - sympA*sympV )
      v_0 = self.sympyToPoly(sympV)
      v_0 = self.Sq_( v_0 )
      t *= 2
    return self.Sq_(v_0)
  def ternary(self, b):
    v = [0]*(self.n-1)

    for i in range(self.n-1):
      coeff_i = 0
      for j in range(8):
        coeff_i +=  2^j * b[ 8*i + j ]
      v[i] = coeff_i

    return self.S3_(v)
  def ternary_plus(self, b):
    v = self.ternary(b)

    t = 0
    for i in range(self.n-2):
      t += v[i]*v[i+1]

    if t < 0:
      s = -1
    else:
      s = 1
      
    i = 0
    while i < self.n-1:
      v[i] = s*v[i]
      i += 2

    v = self.S3_(v)
    
    test = 0
    for v_i in v:
      test += v_i
    
    return v
  def fixed_type(self, b):
    A = [0]*(self.n-1)
    v = [0]*(self.n-1)

    i = 0
    while i < min(self.q/16 - 1, floor(self.n/3)):
      A[i] = 1
      for j in range(30):
        A[i] += 2**(2+j)*b[30*i+j]
      i += 1

    while i < min(self.q/8 - 2, 2*floor(self.n/3)):
      A[i] = 2
      for j in range(30):
        A[i] += 2**(2+j)*b[30*i+j]
      i += 1

    while i < self.n-1:
      for j in range(30):
        A[i] += 2**(2+j)*b[30*i+j]
      i += 1

    A.sort()

    for i in range(self.n-1):
      v[i] = A[i] % 4

    return self.S3_(v)
  def sample_fg(self, fg_bits):

    f_bits = fg_bits[0:self.sample_iid_bits]
    g_bits = fg_bits[self.sample_iid_bits:]

    if self.HRSS:
      f = self.ternary_plus(f_bits)
      g_0 = self.ternary_plus(g_bits)
      gSymp = self.polyToSympy(g_0) * self.polyToSympy(self.phi_1)
      g = self.sympyToPoly(gSymp)
    else:
      f = self.ternary(f_bits)
      g = self.fixed_type(g_bits)
    
        
    if len(f) < self.n:
      f = f + [0]*(self.n-len(f))
    if len(g) < self.n:
      g = g + [0]*(self.n-len(g))
    
    return (f,g)
  def getKey(self, seed):
    seedT = tuple(seed)
    if seedT in self.cache:
      return self.cache[seedT]
    else:
      fg_bits = seed
      f,g = self.sample_fg(fg_bits)
      f_q = self.Sq_inverse(f)
            
      gSymp = self.polyToSympy(g)
      f_qSymp = self.polyToSympy(f_q)
    
      hSymp = gSymp * f_qSymp
      h = self.sympyToPoly(hSymp)
    
      modulus = [-1] + [0]*(self.n-1) + [1]
      h = self.polyMod(h, self.q, modulus)
        
      if len(h) < self.n:
        h = h + [0]*(self.n-len(h))
      
      self.cache[seedT] = (f,g,h)
      
      return (f,g,h)