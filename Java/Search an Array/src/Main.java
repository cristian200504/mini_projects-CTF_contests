import java.util.Scanner;

public class Main
{
    static final Scanner input = new Scanner(System.in);
    public static void main(String[] args)
    {
        System.out.print("How many students? ");
        int  n = input.nextInt();
        if (n <= 0)
        {
            System.out.println("Need at least 1 student.");
            input.close();
            return;
        }

        String[] names = new String[n];
        int[] score = new int[n];
        double sum = 0;
        input.nextLine();
        for (int i = 0; i<score.length; i++)
        {
            System.out.print("Enter student " + (i + 1) + " name: ");
            names[i] = input.nextLine();
            System.out.print("Enter student " + (i + 1) + " score: ");
            score[i] = input.nextInt();
            sum += score[i];
            input.nextLine();
        }
        System.out.printf("--- Summary ---%n");
        for (int i=0;i<score.length;i++)
        {
            System.out.printf("%d) %s: %d%n",i+1,names[i],score[i]);
        }
        System.out.printf("Class average: %.2f%n",(sum/score.length));

        System.out.print("Enter student name to search: ");
        String search = input.nextLine();
        boolean found = false;
        for(int i=0;i<names.length;i++)
        {
            if(names[i].equalsIgnoreCase(search))
            {
                found = true;
                System.out.printf("Found: %s (index %d,score %d)%n",names[i],i,score[i]);
                break;
            }
        }
        if(!found)
        {
            System.out.println("Student " + search + " not found.");
        }
    }
}
