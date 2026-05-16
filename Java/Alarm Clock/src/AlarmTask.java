import java.awt.Toolkit;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Timer;
import java.util.TimerTask;

public class AlarmTask extends TimerTask
{
    private final Timer timer;
    private final ZonedDateTime scheduledTime;

    public AlarmTask(Timer timer, ZonedDateTime scheduledTime)
    {
        this.timer = timer;
        this.scheduledTime = scheduledTime;
    }

    @Override
    public void run()
    {
        DateTimeFormatter fmt = DateTimeFormatter.ofPattern("HH:mm z");

        System.out.println();
        System.out.println("⏰ ALARM! It's " + scheduledTime.format(fmt));

        beepTimes(5);

        timer.cancel();
    }

    private void beepTimes(int times)
    {
        for (int i = 0; i < times; i++)
        {
            try
            {
                Toolkit.getDefaultToolkit().beep();
                Thread.sleep(500);
            }
            catch (Exception e)
            {
                System.out.println("*beep*");
            }
        }
    }
}
