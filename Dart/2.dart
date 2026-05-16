// Problem: Simple Bank Account Management System
//
// Specification:
// Create a simple bank account management system with the following features:
//
// Requirements:
// 1. Create a `BankAccount` class with:
//    - A constructor that takes accountHolderName (String) and initialBalance (double, default 0.0)
//    - Properties: accountHolderName, balance (private), accountNumber (auto-generated unique ID)
//    - Methods: deposit(amount), withdraw(amount), getBalance(), getAccountInfo()
//
// 2. Implement the following business rules:
//    - Deposits must be positive amounts
//    - Withdrawals must be positive amounts and cannot exceed current balance
//    - Balance cannot go below 0
//    - Generate unique account numbers (use a static counter)
//
// 3. Create a `Bank` class that:
//    - Has a list of BankAccount objects
//    - Methods: createAccount(name, initialBalance), findAccount(accountNumber), getTotalBalance()
//
// 4. Handle errors appropriately:
//    - Invalid deposit/withdrawal amounts should throw exceptions or return false
//    - Account not found should return null or appropriate message
//
// 5. Create a main function that demonstrates:
//    - Creating accounts
//    - Making deposits and withdrawals
//    - Displaying account information
//    - Showing total bank balance
//
// Examples:
// - Create account for "John Doe" with $1000
// - Deposit $500 to John's account
// - Withdraw $200 from John's account
// - Display John's account info and total bank balance
//
// Constraints:
// - Account names: 1-50 characters, not empty
// - Amounts: 0.01 to 1000000.00
// - Maximum 100 accounts per bank
//
// Implement the classes and main function below:

class BankAccount {
  // TODO: Implement the BankAccount class according to specifications
  // Hint: Use a static variable for account number generation
  // Use private balance with getter method
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

  // MISSED: Amount validation should check the full range (0.01 to 1000000.00)
  deposit(double amount) {
    if (amount < 0.01 || amount > 1000000.00) {
      throw ArgumentError('Deposit amount must be between 0.01 and 1000000.00');
    }
    _balance += amount;
  }

  // MISSED: Amount validation should check the full range (0.01 to 1000000.00)
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

  // MISSED: getAccountInfo() method was required by spec
  String getAccountInfo() {
    return 'Account Holder: $accountHolderName, Account Number: $accountNumber, Balance: \$$_balance';
  }
}

class Bank {
  // TODO: Implement the Bank class according to specifications
  // Hint: Use a List<BankAccount> to store accounts
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
  // TODO: Implement demonstration code
  // Create a bank, add accounts, perform transactions, display results
  Bank myBank = Bank();
  BankAccount johnAccount = myBank.createAccount('John Doe', 1000.0);
  johnAccount.deposit(500.0);
  johnAccount.withdraw(200.0);
  print('Account Info:');
  print(johnAccount.getAccountInfo());
  print('Total Bank Balance: \$${myBank.getTotalBalance()}');
}
