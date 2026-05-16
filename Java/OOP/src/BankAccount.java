public class BankAccount
{
    private final String ownerName;
    private double balance;
    public BankAccount(String ownerName)
    {
        this.ownerName = ownerName;
        this.balance = 0.0;
    }
    public void deposit(double amount)
    {
        if(amount <= 0) return;
        balance += amount;
    }
    public void withdraw(double amount)
    {
        if (amount <= 0) return;
        if (amount > balance) return;
        balance -= amount;
    }
    public double getBalance()
    {
        return balance;
    }
    public String getOwnerName()
    {
        return ownerName;
    }
}
