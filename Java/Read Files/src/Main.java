import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;

public class Main
{

    // Reads file lines into a list of strings
    public static ArrayList<String> readFile(String filename) throws IOException
    {
        ArrayList<String> lines = new ArrayList<>();

        try (BufferedReader br = new BufferedReader(new FileReader(filename)))
        {
            String line;
            while ((line = br.readLine()) != null)
            {
                lines.add(line);
            }
        }

        return lines;
    }

    // Parses, validates, and reports
    public static String buildReport(ArrayList<String> input, ArrayList<Integer> numbers)
    {
        int errors = 0;
        StringBuilder sb = new StringBuilder();

        sb.append("Invalid entries:");

        for (String s : input)
        {
            try
            {
                if (s == null || s.trim().isEmpty())
                {
                    throw new NumberFormatException();
                }

                int x = Integer.parseInt(s.trim());

                if (x < 0 || x > 100)
                {
                    errors++;
                    sb.append(" ").append(s);
                }
                else
                {
                    numbers.add(x);
                }

            }
            catch (NumberFormatException e)
            {
                errors++;
                sb.append(" ").append(s);
            }
        }

        sb.append("\n");

        if (numbers.isEmpty())
        {
            sb.append("No valid numbers.\n");
        }
        else
        {
            int min = numbers.get(0);
            int max = numbers.get(0);
            long sum = 0;

            for (int x : numbers)
            {
                if (x < min) min = x;
                if (x > max) max = x;
                sum += x;
            }

            double avg = (double) sum / numbers.size();

            sb.append("Valid numbers: ").append(numbers).append("\n");
            sb.append("Count: ").append(numbers.size()).append("\n");
            sb.append("Min: ").append(min).append("\n");
            sb.append("Max: ").append(max).append("\n");
            sb.append("Sum: ").append(sum).append("\n");
            sb.append(String.format("Average: %.2f%n", avg));
        }

        sb.append("Errors: ").append(errors).append("\n");

        return sb.toString();
    }

    public static void main(String[] args)
    {
        try
        {
            ArrayList<String> input = readFile("src/numbers.txt");
            ArrayList<Integer> numbers = new ArrayList<>();

            String report = buildReport(input, numbers);
            System.out.println(report);

        }
        catch (IOException e)
        {
            System.out.println("File read error: " + e.getMessage());
        }
    }
}
