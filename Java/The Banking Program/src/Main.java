import java.util.Scanner;

public class Main
{

    static void showMenu()
    {
        System.out.println("1. Check balance");
        System.out.println("2. Deposit");
        System.out.println("3. Withdraw");
        System.out.println("4. Exit");
        System.out.print("Enter your choice: ");
    }

    static void checkBalance(double balance)
    {
        System.out.printf("Current balance: $%.2f%n", balance);
    }

    static double deposit(double balance, double amount)
    {
        if (amount > 0)
        {
            balance += amount;
        }
        return balance;
    }

    static double withdraw(double balance, double amount)
    {
        if (amount > 0 && amount <= balance)
        {
            balance -= amount;
        }
        return balance;
    }

    public static void main(String[] args) {

        Scanner input = new Scanner(System.in);
        double balance = 0.0;
        boolean active = true;

        while (active)
        {
            showMenu();
            int choice = input.nextInt();

            switch (choice)
            {
                case 1 -> checkBalance(balance);

                case 2 ->
                {
                    System.out.print("Enter amount to deposit: ");
                    double amount = input.nextDouble();
                    balance = deposit(balance, amount);
                }

                case 3 ->
                {
                    System.out.print("Enter amount to withdraw: ");
                    double amount = input.nextDouble();
                    balance = withdraw(balance, amount);
                }

                case 4 ->
                {
                    System.out.println("Bye!");
                    active = false;
                }

                default -> System.out.println("Invalid choice");
            }
        }
        input.close();
    }
}
