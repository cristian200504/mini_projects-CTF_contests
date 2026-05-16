import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

public class Main
{

    public static void writeReport(String text) throws IOException
    {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter("src/report.txt")))
        {
            writer.write(text);
        }
    }

    public static String buildReport(ArrayList<String> input, ArrayList<Integer> numbers)
    {
        int errors = 0;
        StringBuilder sb = new StringBuilder();

        sb.append("Invalid list :");
        for (String s : input)
        {
            try
            {
                int x = Integer.parseInt(s.trim());
                if (0 <= x && x <= 100)
                {
                    numbers.add(x);
                }
                else
                {
                    errors++;
                    sb.append(" ").append(s);
                }
            }
            catch (NumberFormatException | NullPointerException e)
            {
                errors++;
                sb.append(" ").append(s);
            }
        }

        sb.append("\nValid list:");
        for (Integer x : numbers)
        {
            sb.append(" ").append(x);
        }

        sb.append("\nErrors: ").append(errors).append("\n");
        return sb.toString();
    }

    public static void main(String[] args)
    {
        ArrayList<String> input = new ArrayList<>();
        ArrayList<Integer> numbers = new ArrayList<>();

        input.add("10");
        input.add("20");
        input.add("abc");
        input.add("-5");
        input.add("50");
        input.add(null);
        input.add("200");
        input.add("30");
        input.add("");

        String report = buildReport(input, numbers);
        try
        {
            writeReport(report);
            System.out.println("Wrote report.txt");
        }
        catch (IOException e)
        {
            System.out.println("File error: " + e.getMessage());
        }
    }
}
