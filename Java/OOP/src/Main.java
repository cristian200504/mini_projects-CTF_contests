import java.util.Scanner;

public class Main
{
    static Scanner input = new Scanner(System.in);
    static BankAccount bankAccount = new BankAccount("Cristian");
    static void showMenu()
    {
        System.out.println("====== BANK ATM ======");
        System.out.println("0.Exit");
        System.out.println("1.Deposit");
        System.out.println("2.Withdraw");
        System.out.println("3.Show Balance");
        System.out.print("Choose an option: ");
    }
    static boolean runMenu()
    {
        int choice = input.nextInt();
        switch(choice)
        {
            case 0 ->
            {
                System.out.println("Goodbye!");
                return false;
            }
            case 1->
            {
                System.out.print("Enter the amount to deposit: ");
                bankAccount.deposit(input.nextDouble());
            }
            case 2 ->
            {
                System.out.print("Enter the amount to withdraw: ");
                bankAccount.withdraw(input.nextDouble());
            }
            case 3 ->
            {
                System.out.println("Owner: " + bankAccount.getOwnerName());
                System.out.printf("Balance: %.1f$%n",bankAccount.getBalance());
            }
            default -> System.out.println("Invalid option!");
        }
        return true;
    }
    public static void main(String[] args)
    {
        do
        {
            showMenu();
        }while(runMenu());
    }
}
