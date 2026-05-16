def main():
    x =  int(input("What's x? "))
    print(f"x is {x}")
    print(f"x squared is {square(x)}")

def square(x):
    return x * x

if __name__ == "__main__":
    main()