import java.time.Duration;
import java.time.LocalTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;

public class AlarmClock
{
    public static ZonedDateTime computeNextAlarm(LocalTime targetTime, ZoneId zone)
    {
        ZonedDateTime now = ZonedDateTime.now(zone);

        ZonedDateTime candidate =
                now.withHour(targetTime.getHour())
                        .withMinute(targetTime.getMinute())
                        .withSecond(0)
                        .withNano(0);

        if (!candidate.isAfter(now))
        {
            candidate = candidate.plusDays(1);
        }

        return candidate;
    }

    public static long delayMillisUntil(ZonedDateTime when)
    {
        ZonedDateTime now = ZonedDateTime.now(when.getZone());
        Duration d = Duration.between(now, when);

        long ms = d.toMillis();

        if (ms < 0)
        {
            return 0;
        }

        return ms;
    }
}
