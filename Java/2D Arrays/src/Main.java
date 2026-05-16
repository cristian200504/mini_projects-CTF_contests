import java.util.Scanner;

public class Main
{
    public static void main(String[] args)
    {
        Scanner input = new Scanner(System.in);
        int[][] scores = new int[3][3];
        for(int i = 0; i < scores.length; i++)
        {
            for(int j = 0; j < scores[i].length; j++)
            {
                scores[i][j] = input.nextInt();
            }
        }
        for(int i = 0; i < scores.length; i++)
        {
            System.out.printf("Student %d:",i+1);
            for(int j = 0; j < scores[i].length; j++)
            {
                System.out.printf(" %d",scores[i][j]);
            }
            System.out.println();
        }
    }
}
