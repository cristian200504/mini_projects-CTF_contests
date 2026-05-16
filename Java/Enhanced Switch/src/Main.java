import java.util.Scanner;

public class Main
{
    public static void main(String[] args)
    {
        Scanner sc = new Scanner(System.in);

        System.out.println("1 - Celsius to Fahrenheit");
        System.out.println("2 - Fahrenheit to Celsius");
        System.out.println("3 - Exit");
        System.out.print("Enter choice: ");

        int choice = sc.nextInt();
        double temp;
        switch (choice)
        {
            case 1 -> {
                    System.out.print("Enter temperature: ") ;
                temp = sc.nextDouble();
                System.out.printf("%.2f C = %.2f F%n", temp, temp * 1.8 + 32);
                }
            case 2->{
                System.out.print("Enter temperature: ");
                temp  = sc.nextDouble();
                System.out.printf("%.2f F = %.2f C%n",temp,(temp-32)/1.8);
            }
            case 3 -> {
                System.out.println("Goodbye");
            }
            default -> {
                System.out.println("Invalid choice");
            }
        }
        sc.close();
    }
}
