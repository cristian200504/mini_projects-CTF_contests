Looked through the wireshark file for clues and i found something particularly interesting , at first i tried to look for TCP or other unrelated things but then i noticed the HTTP  requests and that stood out to me

after filering out everything exept HTTP requests , one of the four requests had a very long input like somethinng out of a search bar link and i copied that fragment as ASCII and this is what i got

g]q;wE@@lcz]"dPr.[]
6aaUGET /?important=The%20content%20of%20the%20f%20l%20a%20g%20is%20ca314be22457497e81a08fc3bfdbdcd3e0e443c41b5ce9802517b2161aa5e993%20and%20respects%20the%20format HTTP/1.1
Host: example.com
Connection: keep-alive
DNT: 1
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
Accept-Encoding: gzip, deflate
Accept-Language: ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7,it;q=0.6

then looking at this sequence , important=The%20content%20of%20the%20f%20l%20a%20g%20is%20ca314be22457497e81a08fc3bfdbdcd3e0e443c41b5ce9802517b2161aa5e993%20and%20respects%20the%20format HTTP/1.1 stood out to me

so i tried to look for the longest sequence separated by %20 or search spaces and i found ca314be22457497e81a08fc3bfdbdcd3e0e443c41b5ce9802517b2161aa5e993 and knowing that the flag format is CTF{sha256} i had 100% confidence that CTF{ca314be22457497e81a08fc3bfdbdcd3e0e443c41b5ce9802517b2161aa5e993} is the flag

Flag:
**CTF{ca314be22457497e81a08fc3bfdbdcd3e0e443c41b5ce9802517b2161aa5e993}**