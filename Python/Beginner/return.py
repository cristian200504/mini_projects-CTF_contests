
def is_even(number):
    if number % 2 == 0:
        print(f"{number} is even.")
        return True
    else:
        print(f"{number} is odd.")
        return False

def main():
    x=bool(is_even(10))
    print(x)

if __name__ == "__main__":
    main()