import java.util.Scanner;
import java.util.Timer;

public class Main
{
    public static void main(String[] args)
    {
        Scanner scanner = new Scanner(System.in);

        int seconds = readPositiveSeconds(scanner);

        System.out.println("Starting countdown...");

        Timer timer = new Timer();
        CountdownTask task = new CountdownTask(timer, seconds);

        long delayMs = 0;
        long periodMs = 1000;

        timer.scheduleAtFixedRate(task, delayMs, periodMs);
    }

    private static int readPositiveSeconds(Scanner scanner)
    {
        while (true)
        {
            System.out.print("Enter countdown seconds: ");
            String s = scanner.nextLine().trim();

            try
            {
                int value = Integer.parseInt(s);

                if (value <= 0)
                {
                    System.out.println("Please enter a number > 0.");
                    continue;
                }

                return value;
            }
            catch (NumberFormatException e)
            {
                System.out.println("Please enter a valid integer.");
            }
        }
    }
}
