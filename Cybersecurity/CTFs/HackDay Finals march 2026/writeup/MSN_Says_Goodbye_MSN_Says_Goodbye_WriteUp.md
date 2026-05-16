# Write-up: MSN Says Goodbye

**Category:** Crypto / Steganography
**Flag:** `HACKDAY{xX_Pr1m3_Xx}`

## Challenge Overview
We were provided with an exported MSN Messenger chat history (`ChatHistory_2003-11-15.xml`), a custom emoticon pack with a `README.txt`, a folder containing `avatars`, and a mysterious encrypted file called `secret_message.enc`. Our goal was to decipher the hidden clues and successfully decrypt the secret message to retrieve the flag.

## Step 1: Analyzing the Chat History & Emoticons
The first lead comes from a conversation thread where the user `~xX_D4rK_Adm1n_Xx~` sends a bunch of seemingly random custom emoticons.

Looking closely at `emoticon_pack_README.txt`, we can see a mapped `Letter` column for each custom emoticon. By noting down the exact sequence of non-standard emoticons used exclusively in the chat, we can map them back to their respective letters:

* `(L)` → **L**
* `(S)` → **S**
* `(B)` → **B**
* `(#)` → **[space]**
* `(B)` → **B**
* `(L)` → **L**
* `(U)` → **U**
* `(E)` → **E**
* `(Q)` → **[space]**
* `(P)` → **P**
* `(R)` → **R**
* `(I)` → **I**
* `(M)` → **M**
* `(E)` → **E**
* `(Z)` → **S**

Concatenating them in order spells out the hidden instruction: **`LSB BLUE PRIMES`**. 
During the exchange, the user `Sk8erBoi_Tony` says: *"c quoi le rapport avec les avatars la mdr"* (what does this have to do with the avatars lol), directly pointing our instruction towards the 4 provided avatar images.

## Step 2: Extracting LSB Payloads
The phrase **`LSB BLUE PRIMES`** instructs us to extract the **L**east **S**ignificant **B**it of the **Blue** color channel from pixels situated at **Prime** indices sequentially (i.e. indices 2, 3, 5, 7, 11...). 

Since "avatars" is plural, the extraction applies to all 4 avatar files.

Writing a short Python script to parse the bits reveals a structured format natively hidden inside the LSB sequence of each avatar:
1. The first 16 bits encode an integer representing a length: `0x0009` (9 bytes).
2. The following 72 bits consist of the 9-byte payload.

Dumping the payloads of each avatar reveals:
* `dark_admin.bmp`: `\x00\x98\x11\x16\xadBd\xc9\r`
* `princess2003.bmp`: `\x01\x1b\xe3\xcc\xd6PE\n\xa6`
* `neo_hacker.bmp`: `\x02\x93\xd9\xd34\xb9#<\x08`
* `sk8erboi.bmp`: `\x03*]\xdbAj\xed\x0c\x0c`

## Step 3: Constructing the AES Key
We immediately notice that the first byte of each payload acts as a chunk index (`\x00`, `\x01`, `\x02`, `\x03`).
By stripping this indexing byte and concatenating the remaining 8 bytes from each chunk in order, we build a continuous 32-byte sequence. 

32 bytes is exactly 256 bits — the optimal length required for an **AES-256** encryption key.

## Step 4: Final Decryption
Looking at the header comments inside `ChatHistory_2003-11-15.xml`, we are served the final structural clues for decryption:
`<!-- Encryption: aes-256-cbc / IV: md5(admin_nickname) -->`

We calculate the MD5 hash of the admin's MSN nickname (`~xX_D4rK_Adm1n_Xx~`), resulting in the 16-byte Initialization Vector (IV):
`9873e5aefa32ab315754767a419bf1bd`

Using standard **AES-256-CBC**, we provide our dynamically reconstructed 32-byte key along with the derived IV to decrypt the `secret_message.enc` file. 

The binary padding naturally drops out, revealing the final underlying plaintext:
`HACKDAY{xX_Pr1m3_Xx}`
