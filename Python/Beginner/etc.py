def main():
    balance = 1000
    print({"Balance": balance})
    withdraw = int(input("Withdraw: "))
    if withdraw > balance:
        print("Insufficient funds")
    else:
        balance -= withdraw
        print({"Balance": balance})

def balance():
    balance = 1000
    print({"Balance": balance})
    withdraw = int(input("Withdraw: "))
    if withdraw > balance:
        print("Insufficient funds")
    else:
        balance -= withdraw
        print({"Balance": balance})

def withdraw():
    balance = 1000
    print({"Balance": balance})
    withdraw = int(input("Withdraw: "))
    if withdraw > balance:
        print("Insufficient funds")
    else:
        balance -= withdraw
        print({"Balance": balance})

class Account:
    def __init__(self, balance):
        self.balance = balance

    def withdraw(self, amount):
        if amount > self.balance:
            print("Insufficient funds")
        else:
            self.balance -= amount
            print({"Balance": self.balance})

if __name__ == "__main__":
    main()            