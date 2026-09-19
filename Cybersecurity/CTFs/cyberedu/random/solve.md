so i first downloaded a file named main and i immediately noticed that it didnt have any sort of filetype so i opened it with binary ninja and got to the main function to traceback how the flag was made and i found this:

00401249    int32_t main(int32_t argc, char** argv, char** envp)

00401255        void* fsbase
00401255        int64_t rax = *(fsbase + 0x28)
0040127d        setvbuf(fp: stdin, buf: nullptr, mode: 2, size: 0)
0040129b        setvbuf(fp: stdout, buf: nullptr, mode: 2, size: 0)
004012b9        setvbuf(fp: stderr, buf: nullptr, mode: 2, size: 0)
004012ca        srand(x: time(nullptr))
004012d9        puts(str: "Menu: \n1. Generate number")
004012f4        int32_t var_14
004012f4        __isoc99_scanf(format: "%d", &var_14)
004012f9        int32_t rax_3 = var_14
004012f9        
004012ff        if (rax_3 == 1)
00401320            printf(format: "%d", zx.q(rand()))
004012ff        else if (rax_3 == 0x539)
00401348            printf(format: "%s", getenv(name: "FLAG"))
00401306        else
0040135e            printf(format: "wrong option")
0040135e        
0040136c        *(fsbase + 0x28)
0040136c        
00401375        if (rax == *(fsbase + 0x28))
0040137d            return 0
0040137d        
00401377        __stack_chk_fail()
00401377        noreturn


looking at the elif statement i noticed that in order for me to get the flag my input should be 539 hexadecimal which translates to 1337

so i opened the instance and i typed 1337 and i got the flag

┌──(santey22㉿DESKTOP-4L8F315)-[~]
└─$ nc 34.179.231.75 31215
Menu:
1. Generate number
1337
flag{l33t_m3_to_g3t_th3_flag}


flag:
**flag{l33t_m3_to_g3t_th3_flag}**