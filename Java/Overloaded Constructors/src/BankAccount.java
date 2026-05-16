public class BankAccount
{

    private final String name;
    private final double balance;

    public BankAccount(String name)
    {
        this(name, 0.0);
    }

    public BankAccount(String name, double balance)
    {
        this.name = name;
        this.balance = balance;
    }

    public void displayInfo()
    {
        System.out.println("Name: " + name);
        System.out.println("Balance: $" + balance);
    }
}
