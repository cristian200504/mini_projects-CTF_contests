import java.util.Timer;
import java.util.TimerTask;

public class CountdownTask extends TimerTask
{
    private int secondsLeft;
    private final Timer timer;

    public CountdownTask(Timer timer, int secondsLeft)
    {
        this.timer = timer;
        this.secondsLeft = secondsLeft;
    }

    @Override
    public void run()
    {
        if (secondsLeft > 0)
        {
            System.out.println("Time left: " + secondsLeft + " seconds");
            secondsLeft--;
        }
        else
        {
            System.out.println("TIME'S UP!");
            timer.cancel();
        }
    }
}
