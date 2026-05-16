import javax.accessibility.AccessibleAction;
import java.util.Scanner;

public class Main
{
    public static void main(String[] args)
    {
        Scanner sc = new Scanner(System.in);

        System.out.print("Enter temperature: ");
        double temp = sc.nextDouble();

        System.out.print("Enter choice (1 = C->F, 2 = F->C): ");
        int choice = sc.nextInt();

        if(choice != 1 && choice != 2)
        {
            System.out.println("Invalid choice");
            sc.close();
            return;
        }
        switch(choice)
        {
            case 1:
                System.out.printf("%.2f C = %.2f F", temp, temp * 1.8 +32);
                break;
            case 2:
                System.out.printf("%.2f F = %.2f C",temp,(temp-32)/1.8);
                break;
        }
        sc.close();
    }
}
