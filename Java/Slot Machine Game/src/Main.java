import java.util.Arrays;
import java.util.Random;
import java.util.Scanner;

public class Main
{
    static Scanner sc = new Scanner(System.in);
    static Random rand = new Random();
    static int StartBalance = 100;
    static int randomGeneration()
    {
        return rand.nextInt(4);
    }
    static boolean continueGame()
    {
        System.out.print("Wanna play?(y/n) ");
        return sc.nextLine().equals("y");
    }
    static void printMenu(String[] Symbols,int[] Variable) {
        int[] Count = new int[4];
        StartBalance -= 10;
        for (int i = 0; i < 3; ++i)
        {
            Variable[i] = randomGeneration();
            Count[Variable[i]]++;
            if (i == 0) System.out.printf("%s ", Symbols[Variable[i]]);
            else if (i == 1) System.out.printf("| %s |", Symbols[Variable[i]]);
            else System.out.printf(" %s", Symbols[Variable[i]]);
        }
        Arrays.sort(Count);
        System.out.println();
        switch (Count[3])
        {
            case 1 -> System.out.println("You lose!");
            case 2 -> {
                System.out.println("Small win!");
                StartBalance+=20;
            }
            case 3 ->
            {
                System.out.println("Jackpot!");
                StartBalance+=50;
            }
            default -> System.out.println("Error");
        }
        System.out.println("Balance: " + StartBalance);
        System.out.println("--------------------");
    }
	public static void main(String[] args)
	{
        String[] Symbols = {"CHERRY", "LEMON" , "BELL", "STAR"};
        int[] Variable= new int[3];
        while(continueGame() && StartBalance >= 10)
        {
            printMenu(Symbols,Variable);
        }
        System.out.println("Thanks for playing!");
    }
}
