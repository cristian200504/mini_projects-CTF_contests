import java.util.Timer;

public class Main
{
    public static void main(String[] args)
    {
        System.out.println("Starting...");

        Timer timer = new Timer();
        TickTask task = new TickTask(timer, 10);

        long delayMs = 0;
        long periodMs = 1000;

        timer.scheduleAtFixedRate(task, delayMs, periodMs);
    }
}
