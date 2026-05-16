public class BankAccount
{
    final private String name;
    final private double balance;
    public BankAccount(String name,double balance)
    {
        this.name=name;
        this.balance=balance;
    }
    public void displayInfo()
    {
        System.out.println("Name: "+name);
        System.out.println("Balance: $"+balance);
    }
}
