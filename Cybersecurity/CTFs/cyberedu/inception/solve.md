saw the image and the category misc i immediately used aperi solver and noticed that at the binwalk section the image contained files inside so i ran locally the command and i got:

└─$ binwalk chall.jpeg

DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
0             0x0             JPEG image data, JFIF standard 1.01
382           0x17E           Copyright string: "Copyright (c) 1998 Hewlett-Packard Company"
110955        0x1B16B         PNG image, 400 x 400, 1-bit colormap, non-interlaced
111014        0x1B1A6         Zlib compressed data, default compression

then i immediately went for the extraction  with binwalk --dd='.*' chall.jpeg 
and i got many files but my focus was on 1B16B and i renamed it to 1B16B.png and it transformed into a qr code and after scanning the qr code i got the flag:
**DCTF{394a6dc71dee0bc7de700d28da66c836a534a72d417b1f25b6776d35a82b07f0}**