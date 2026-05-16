def get_age():
    while True:
        try:
            age = int(input("How old are you?"))
            print(f"You are {age} years old.")
            return age
        except ValueError:
            print("Invalid input. Please enter a number.")

def main():
    age = get_age()
    print("unrelated to exception handling")

main()