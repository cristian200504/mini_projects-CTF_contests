import java.util.Scanner;

public class Main
{
    public static void main(String[] args)
    {
        Scanner input = new Scanner(System.in);
        int num1,num2,sum;
        double quo;
        System.out.print("Enter first number: ");
        num1 = input.nextInt();
        System.out.print("Enter second number: ");
        num2 = input.nextInt();
        sum =num1 + num2;
        quo = (double)num1/num2;
        System.out.println("Sum: " + sum);
        System.out.println("Difference: " + Math.abs(num1 - num2));
        System.out.println("Product: " + num1 * num2);
        System.out.println("Quotient: " + quo);
        System.out.println("Remainder: " + num1 % num2);
        input.close();
    }
}
