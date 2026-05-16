def hello(to="World"):
    print("Hello", to.strip().title())
def power(base, exponent):
    return base ** exponent
def main():
    hello(input("Type name: "))
    print("power(2, 3) =", power(2, 3))

if __name__ == "__main__":
    main()