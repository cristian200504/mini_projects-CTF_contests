import java.util.Scanner;

public class Main
{
    public static void main(String[] args)
    {
        Scanner input = new Scanner(System.in);
        double pri,rate;
        int times,years;
        System.out.print("Enter principal: ");
        pri = input.nextDouble();
        System.out.print("Enter interest rate (%): ");
        rate = input.nextDouble();
        rate /= 100;
        System.out.print("Enter times compounded per year: ");
        times = input.nextInt();
        System.out.print("Enter years: ");
        years = input.nextInt();
        double amount = pri * Math.pow(1 + rate / times, times * years);
        System.out.printf("Final amount: $%.2f%n",amount);
        input.close();
    }
}
