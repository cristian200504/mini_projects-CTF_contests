import java.util.Scanner;

public class Main
{
    public static void main(String[] args)
    {

        Scanner input = new Scanner(System.in);
        int sum = 0;
        int variable = -1;
        while(variable != 0)
        {
            variable = input.nextInt();
            if(variable < 0)
            {
                System.out.println("Skipping negative number");
                continue;
            }
            else
            {
                sum += variable;
            }
        }
        System.out.println("sum = " + sum);

        input.close();
    }
}
