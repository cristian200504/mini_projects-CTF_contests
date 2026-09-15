first of all i extracted the values separately:
\x00 \x00 \x00 \x18 C _ \x05 E V T F U R B _ U G _ V \x17 V S @ \x03 [ C \x02 \x07 C Q S M \x02 P M _ S \x12 V \x07 B V Q \x15 S T \x11 _ \x05 A P \x02 \x17 R Q L \x04 P E W P L \x04 \x07 \x15 T V L \x1b

then i translated everything to hex

00 00 00 18 43 5f 05 45 56 54 46 55 52 42 5f 55 47 5f 56 17 56 53 40 03 5b 43 02 07 43 51 53 4d 02 50 4d 5f 53 12 56 07 42 56 51 15 53 54 11 5f 05 41 50 02 17 52 51 4c 04 50 45 57 50 4c 04 07 15 54 56 4c 1b

and then concatenated everything
00000018435f05455654465552425f55475f5617565340035b4302074351534d02504d5f53125607425651155354115f054150021752514c04504557504c04071554564c1b

now since i know that the flag format is ctf{sha256} and the first 3 hex values are 0 and A xor 0 is A that means that the key must be CTF

so I entered the website
https://www.dcode.fr/xor-cipher

and i used the text: 00000018435f05455654465552425f55475f5617565340035b4302074351534d02504d5f53125607425651155354115f054150021752514c04504557504c04071554564c1b

and the ascii key as "ctf"

so i clicked decrypt and the xor between the two happened and i got the flag:
**ctf{79f107231696395c004e87dd7709d3990f0d602a57e9f56ac428b31138bda258}**
