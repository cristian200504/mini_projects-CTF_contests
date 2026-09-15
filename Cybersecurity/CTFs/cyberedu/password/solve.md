downloaded chall.pyc

and since its a pyc i immediately went for an online decompiler:
https://www.decompiler.com/python

placed the file here and got the following code:
# Source Generated with Decompyle++
# File: chall.pyc (Python 2.7)

a = 'DCTF{09fa'
c = '4d3142a6a'
b = '7ab70e9aa'
f = '1929d62e0'
g = '805934d86'
d = 'd4b55ea5b'
e = '1a436b536'
h = '59eadd}'
flag = a + b + c + d + e + f + g + h
password = 'Pass999990000!!!))))'
print 'Enter the password: '
buf = raw_input()
if password == buf:
    print flag
else:
    print 'Wrong password!'

as soon as i saw this i ordered the variables and deleted everything else and got:
a = 'DCTF{09fa'
b = '7ab70e9aa'
c = '4d3142a6a'
d = 'd4b55ea5b'
e = '1a436b536'
f = '1929d62e0'
g = '805934d86'
h = '59eadd}'

then i deleted all variables and = and ' signs and concatenated the flag and the final result was:
**DCTF{09fa7ab70e9aa4d3142a6ad4b55ea5b1a436b5361929d62e0805934d8659eadd}**