import java.util.Scanner;

public class Main
{
    public static void main(String[] args)
    {
        for (TrafficLight light : TrafficLight.values())
        {
            System.out.println(light + " lasts " + light.getDurationSeconds() + " seconds");
        }

        Scanner scanner = new Scanner(System.in);
        System.out.print("\nEnter a traffic light (RED, YELLOW, GREEN): ");
        String input = scanner.nextLine().trim().toUpperCase();

        try
        {
            TrafficLight selected = TrafficLight.valueOf(input);
            System.out.println(selected + " duration: " + selected.getDurationSeconds() + " seconds");
        }
        catch (IllegalArgumentException e)
        {
            System.out.println("Invalid traffic light.");
        }
    }
}
