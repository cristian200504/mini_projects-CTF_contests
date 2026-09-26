first of all i downloaded the image
then i tried aperi solve and i noticed that there was no visual steganography and i saw the contents of the image being a password survey and i immediately thought of steghide/stegcracker and i decided to use stegcracker bc its much more effective when dealing with lots of passwords so i wrote a wordlist.txt file and it contained:

123
1234
asdf
11111
4321
password
god
aaaa
AAAA
osfp
OSFP
aek
AEK
paok
PAOK
pao
PAO
αεκ
οσφπ
παοκ
παο
other football team
$#@!
!@#$
Mercedes
xxxxxx
xxxxxxx
xxxxxxxx
FireB@!!
Batman
A&%T2h
mercedes
@Sfalel@
@Șfalel@
qwertyui
123456

then i used the command stegcracker quals_warmup_out-of-the-image_Simple-Survey.jpg wordlist.txt and it found qwertyui as the password and looking at quals_warmup_out-of-the-image_Simple-Survey.jpg.out you can see the flag

flag:
**ECSC{8bcaac73afa8c3a40f089ce451e1a157ba734e3a34189ddfeb32a0f709dca28c}**