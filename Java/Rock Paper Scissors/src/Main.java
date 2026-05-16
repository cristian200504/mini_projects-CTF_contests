import java.util.Random;
import java.util.Scanner;

public class Main
{
    static Scanner sc = new Scanner(System.in);
    static Random rand = new Random();
    static int randomGeneration()
    {
        return rand.nextInt(3);
    }
    static void determineWinner(int player, int computer, String[] choices)
    {
        if (player == computer)
        {
            System.out.println("Tie!");
        }
        else if (player == (computer + 1) % 3)
        {
            System.out.println("You win!");
        }
        else
        {
            System.out.println("You lose!");
        }
    }

    public static void main(String[] args)
	{
        String[] choices = {"rock","paper","scissors"};
        int player = randomGeneration();
        int computer = randomGeneration();
        System.out.printf("My pick: %s%n",choices[player]);
        System.out.printf("Computer: %s%n",choices[computer]);
        determineWinner(player,computer,choices);
	}
}
