import java.util.Scanner;

public class Main
{
    static void printScore(int score)
    {
        System.out.printf("Score: %d%n",score);
    }
    static void printScore(int score,int max)
    {
        System.out.printf("Score %d/%d%n", score, max);
    }
    static void printScore(String name,int score)
    {
        System.out.printf("%s scored %d%n",name , score);
    }
    public static void main(String[] args)
    {
        Scanner input = new Scanner(System.in);
        int score = 82 , max = 100;
        String name = "Alex";
        printScore(score);
        printScore(score,max);
        printScore(name,score);
    }
}
