import java.util.Scanner;

public class Main
{
    static final Scanner input = new Scanner(System.in);
	public static void main(String[] args)
    {
        System.out.print("How many scores? ");
        int  n = input.nextInt();
        if (n <= 0)
        {
            System.out.println("Need at least 1 score.");
            input.close();
            return;
        }
        int[] score = new int[n];
        System.out.print("Enter score 1: ");
        score[0] = input.nextInt();

        int min = score[0] , max = score[0];
        double sum = score[0];
        for (int i = 1; i<score.length; i++)
        {
            System.out.print("Enter score " + (i + 1) + ": ");
            score[i] = input.nextInt();
            sum += score[i];
            if(score[i] >= max)
            {
                max = score[i];
            }
            if(score[i] <= min)
            {
                min = score[i];
            }
        }
        System.out.print("Scores:");
        for (int i : score)
        {
            System.out.printf(" %d", i);
        }
        System.out.printf("%nAverage: %.2f%n",(sum/score.length));
        System.out.printf("Highest: %d%n",max);
        System.out.printf("Lowest: %d%n",min);
	}
}
