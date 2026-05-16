import java.util.Scanner;

public class Main
{
	public static void main(String[] args)
	{
        BankAccount account1 = new BankAccount("Alex", 1500.50);
        BankAccount account2 = new BankAccount("Jamie", 300.00);

        account1.displayInfo();
        System.out.println();
        account2.displayInfo();
	}
}
