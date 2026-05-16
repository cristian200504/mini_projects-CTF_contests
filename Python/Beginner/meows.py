def meow(n: int) -> str:
    return "meow\n" * n

number :int = int(input("Enter the number of meows: "))
meows :str = meow(number)
print(meows , end="")