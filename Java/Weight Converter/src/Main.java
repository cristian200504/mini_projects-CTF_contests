import java.util.Scanner;

public class Main
{
    public static void main(String[] args)
    {
        Scanner sc = new Scanner(System.in);

        System.out.print("Enter weight: ");
        double convert=1,weight = sc.nextDouble();
        if(weight < 0)
        {
            System.out.println("Invalid weight");
            sc.close();
            return;
        }
        System.out.print("Enter choice (1 = lbs->kg, 2 = kg->lbs): ");
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
                convert=weight/2.205;
                System.out.printf("%.2f lbs = %.2f kg%n",weight,convert);
                break;
            case 2:
                convert=weight*2.205;
                System.out.printf("%.2f kg = %.2f lbs%n",weight,convert);
                break;
        }
        sc.close();
    }
}
