import java.util.Timer;
import java.util.TimerTask;

public class TickTask extends TimerTask
{
    private int secondsPassed;
    private final int limitSeconds;
    private final Timer timer;

    public TickTask(Timer timer, int limitSeconds)
    {
        this.timer = timer;
        this.limitSeconds = limitSeconds;
        this.secondsPassed = 0;
    }

    @Override
    public void run()
    {
        secondsPassed++;
        System.out.println("Tick: " + secondsPassed);

        if (secondsPassed >= limitSeconds)
        {
            System.out.println("Done!");
            timer.cancel();
        }
    }
}
