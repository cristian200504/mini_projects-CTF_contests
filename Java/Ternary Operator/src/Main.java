import java.util.Scanner;

public class Main
{
    public static void main(String[] args)
    {
        Scanner sc = new Scanner(System.in);

        System.out.print("Enter score: ");
        int score = sc.nextInt();
        if(score<0)
        {
            sc.close();
            System.out.println("Invalid score");
            return;
        }
        System.out.print("Bonus credit? (true/false): ");
        boolean bonus = sc.nextBoolean();

        score=bonus?score+5:score;
        String cal =(score >=60)?"Pass":"Fail";
        System.out.printf("%s%n",cal);

        sc.close();
    }
}

