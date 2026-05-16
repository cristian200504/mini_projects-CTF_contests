import java.util.Random;

public class Main
{
    public static void main(String[] args)
    {
        Random random = new Random();
        int x , y;
        x=random.nextInt(6)+1;
        y=random.nextInt(6)+1;
        System.out.println("Dice 1: "+x);
        System.out.println("Dice 2: "+y);
        if(x+y >= 10)
        {
            System.out.println("You win");
        }
        else
        {
            System.out.println("You lose");
        }
    }
}
