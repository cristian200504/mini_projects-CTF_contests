import java.util.Scanner;

public class Main
{
    public static void main(String[] args)
    {
        Scanner input = new Scanner(System.in);
        int choice;
        double num1 = 0, num2 = 0;
        while(true)
        {
            System.out.println("===== SMART CALCULATOR =====");
            System.out.println("1 - Addition");
            System.out.println("2 - Subtraction");
            System.out.println("3 - Multiplication");
            System.out.println("4 - Division");
            System.out.println("5 - Modulus");
            System.out.println("6 - Exit");
            System.out.print("Choose an option: ");
            choice = input.nextInt();
            if (choice == 6)
            {
                System.out.println("Calculator closed.");
                input.close();
                break;
            }
            if(choice <=5 && choice >=1)
            {
                System.out.printf("%nEnter first number: ");
                num1 = input.nextDouble();
                System.out.printf("%nEnter second number: ");
                num2 = input.nextDouble();
                System.out.printf("%n");
            }
            switch(choice)
            {
                case 1 ->{
                    System.out.printf("%.2f%n",num1+num2);
                }
                case 2 ->{
                    System.out.printf("%.2f%n",num1-num2);
                }
                case 3 ->{
                    System.out.printf("%.2f%n",num1*num2);
                }
                case 4 ->{
                    if (num2 == 0) System.out.println("Error: Cannot divide by zero");
                    else System.out.printf("%.2f%n",num1/num2);
                }
                case 5 ->{
                    if (num2 == 0) System.out.println("Error: Cannot modulus by zero");
                    else System.out.printf("%.2f%n",num1%num2);
                }
                default ->{
                    System.out.println("Invalid choice!");
                }
            }
        }
    }
}
