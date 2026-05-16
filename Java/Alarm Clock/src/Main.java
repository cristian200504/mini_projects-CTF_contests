import java.time.LocalTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.Scanner;
import java.util.Timer;

public class Main
{
    public static void main(String[] args)
    {
        Scanner scanner = new Scanner(System.in);

        ZoneId zone = readZone(scanner);
        LocalTime alarmTime = readTime(scanner);

        ZonedDateTime nextAlarm = AlarmClock.computeNextAlarm(alarmTime, zone);
        long delayMs = AlarmClock.delayMillisUntil(nextAlarm);

        DateTimeFormatter fmt = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm z");

        System.out.println();
        System.out.println("Now:        " + ZonedDateTime.now(zone).format(fmt));
        System.out.println("Alarm set:  " + nextAlarm.format(fmt));
        System.out.println("Delay ms:   " + delayMs);

        Timer timer = new Timer();
        timer.schedule(new AlarmTask(timer, nextAlarm), delayMs);
    }

    private static ZoneId readZone(Scanner scanner)
    {
        while (true)
        {
            System.out.print("Enter timezone (e.g., Europe/Bucharest): ");
            String s = scanner.nextLine().trim();

            try
            {
                return ZoneId.of(s);
            }
            catch (Exception e)
            {
                System.out.println("Invalid timezone ID.");
            }
        }
    }

    private static LocalTime readTime(Scanner scanner)
    {
        DateTimeFormatter timeFmt = DateTimeFormatter.ofPattern("HH:mm");

        while (true)
        {
            System.out.print("Enter alarm time (HH:mm): ");
            String s = scanner.nextLine().trim();

            try
            {
                return LocalTime.parse(s, timeFmt);
            }
            catch (DateTimeParseException e)
            {
                System.out.println("Invalid time format.");
            }
        }
    }
}
