# Lost and Found CTF Flag

The flag for the Lost and Found CTF challenge is:

**`UMASS{h3r35_7h3_c4rg0_vr00m}`**

### Summary of Solution
- **Encryption**: Cyclic XOR with a 165-byte key.
- **Key Recovery**: Derived from disk forensics (offset `2410870272` in `2.img`) and git index analysis.
- **Discovery**: The flag was found in the commit message of commit `55a10e08` after decrypting the git objects.
