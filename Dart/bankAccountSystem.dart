class BankAccount {
  String accountHolderName;
  late double _balance;
  late int accountNumber;
  static int _accountNumberCounter = 0;

  BankAccount(this.accountHolderName, [this._balance = 0.0]) {
    _accountNumberCounter++;
    this.accountNumber = _accountNumberCounter;
    this.accountHolderName = accountHolderName;
    this._balance = _balance;
  }

  double getBalance() {
    return _balance;
  }

  deposit(double amount) {
    if (amount < 0.01 || amount > 1000000.00) {
      throw ArgumentError('Deposit amount must be between 0.01 and 1000000.00');
    }
    _balance += amount;
  }

  withdraw(double amount) {
    if (amount < 0.01 || amount > 1000000.00) {
      throw ArgumentError(
        'Withdrawal amount must be between 0.01 and 1000000.00',
      );
    }
    if (amount > _balance) {
      throw ArgumentError('Insufficient funds');
    }
    _balance -= amount;
  }

  String getAccountInfo() {
    return 'Account Holder: $accountHolderName, Account Number: $accountNumber, Balance: \$$_balance';
  }
}

class Bank {
  List<BankAccount> accounts = [];
  createAccount(String name, [double initialBalance = 0.0]) {
    if (accounts.length >= 100) {
      throw Exception('Maximum number of accounts reached');
    }
    if (name.isEmpty || name.length > 50) {
      throw ArgumentError(
        'Account holder name must be between 1 and 50 characters',
      );
    }
    BankAccount newAccount = BankAccount(name, initialBalance);
    accounts.add(newAccount);
    return newAccount;
  }

  findAccount(int accountNumber) {
    try {
      return accounts.firstWhere(
        (account) => account.accountNumber == accountNumber,
      );
    } catch (e) {
      return null;
    }
  }

  getTotalBalance() {
    return accounts.fold(0.0, (total, account) => total + account.getBalance());
  }
}

void main() {
  Bank myBank = Bank();
  BankAccount johnAccount = myBank.createAccount('John Doe', 1000.0);
  johnAccount.deposit(500.0);
  johnAccount.withdraw(200.0);
  print('Account Info:');
  print(johnAccount.getAccountInfo());
  print('Total Bank Balance: \$${myBank.getTotalBalance()}');
}
