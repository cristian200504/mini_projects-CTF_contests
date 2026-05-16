import java.util.Scanner;

public class Main
{
    static final Scanner input = new Scanner(System.in);
    static int max(int... values)
    {
        int max = values[0];
        for (int value : values)
        {
            if (value > max)
            {
                max = value;
            }
        }
        return max;
    }
    static void printStudents(String title, String... names)
    {
        System.out.println(title);
        for(int i = 0; i < names.length; i++)
        {
            System.out.printf("%d) %s%n",i+1,names[i]);
        }
    }
    public static void main(String[] args)
    {
        System.out.print("How many students? ");
        String[] names = new String[input.nextInt()];
        int[] values = new int[names.length];
        input.nextLine();
        for(int i = 0; i < names.length; i++)
        {
            System.out.printf("Student %d name:  ",i+1);
            names[i] = input.nextLine();
            System.out.printf("Student %d score:  ",i+1);
            values[i] = input.nextInt();
            input.nextLine();
        }
        printStudents("==== Students ====",names);
        int max = max(values);
        System.out.println("Max student score: " + max);
    }
}
