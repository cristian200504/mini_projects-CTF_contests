import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.Period;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.Scanner;

public class Main
{
    public static void main(String[] args)
    {
        Scanner scanner = new Scanner(System.in);

        DateTimeFormatter dateFmt = DateTimeFormatter.ofPattern("yyyy-MM-dd");
        DateTimeFormatter timeFmt = DateTimeFormatter.ofPattern("HH:mm");
        DateTimeFormatter outFmt = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm z");

        LocalDate date = readDate(scanner, dateFmt);
        LocalTime time = readTime(scanner, timeFmt);
        ZoneId zone = readZone(scanner);
        long minutes = readMinutes(scanner);

        LocalDateTime localStart = LocalDateTime.of(date, time);
        ZonedDateTime start = ZonedDateTime.of(localStart, zone);
        ZonedDateTime end = start.plusMinutes(minutes);

        Instant utcInstant = start.toInstant();
        ZonedDateTime newYork = start.withZoneSameInstant(ZoneId.of("America/New_York"));

        LocalDate todayInZone = ZonedDateTime.now(zone).toLocalDate();
        Period until = Period.between(todayInZone, date);

        System.out.println();
        System.out.println("Appointment start: " + start.format(outFmt));
        System.out.println("Appointment end:   " + end.format(outFmt));
        System.out.println("As UTC Instant:    " + utcInstant);
        System.out.println("As New York time:  " + newYork.format(outFmt));
        System.out.println("Days until:        " + until.getDays() + " (Period = " + until + ")");
    }

    private static LocalDate readDate(Scanner scanner, DateTimeFormatter dateFmt)
    {
        while (true)
        {
            System.out.print("Enter date (yyyy-MM-dd): ");
            String s = scanner.nextLine().trim();

            try
            {
                return LocalDate.parse(s, dateFmt);
            }
            catch (DateTimeParseException e)
            {
                System.out.println("Invalid date format.");
            }
        }
    }

    private static LocalTime readTime(Scanner scanner, DateTimeFormatter timeFmt)
    {
        while (true)
        {
            System.out.print("Enter time (HH:mm): ");
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

    private static long readMinutes(Scanner scanner)
    {
        while (true)
        {
            System.out.print("Enter duration in minutes: ");
            String s = scanner.nextLine().trim();

            try
            {
                long minutes = Long.parseLong(s);

                if (minutes <= 0)
                {
                    System.out.println("Minutes must be > 0.");
                    continue;
                }

                return minutes;
            }
            catch (NumberFormatException e)
            {
                System.out.println("Please enter a valid number.");
            }
        }
    }
}
