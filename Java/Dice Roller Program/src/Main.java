import java.util.Random;
import java.util.Scanner;

public class Main
{
    static final Random random = new Random();
    static int rollDie(int sides)
    {
        return random.nextInt(sides) + 1;
    }
    static void rollDice(int numberOfDice, int sides)
    {
        int sum = 0,result;
        for(int i = 1; i <= numberOfDice; i++)
        {
            result = rollDie(sides);
            System.out.printf("Dice %d rolled: %d\n",i, result);
            sum += result;
        }
        System.out.printf("Total: %d", sum);
    }
    public static void main(String[] args)
    {
        Scanner input = new Scanner(System.in);
        System.out.print("How many dice? ");
        int numberOfDice = input.nextInt();
        System.out.print("How many sides per dice? ");
        int sides = input.nextInt();
        rollDice(numberOfDice, sides);
    }
}
