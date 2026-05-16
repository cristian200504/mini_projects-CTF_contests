import java.util.ArrayList;

public class Main
{

    public static ArrayList<Integer> parseValidIntegers(ArrayList<String> input)
    {
        ArrayList<Integer> valid = new ArrayList<>();

        for (String s : input) {
            try
            {
                valid.add(Integer.parseInt(s.trim()));
            }
            catch (NumberFormatException nfe)
            {

            }
        }
        return valid;
    }

    public static void printAnalysis(ArrayList<Integer> nums)
    {
        if (nums.isEmpty())
        {
            System.out.println("No valid numbers.");
            return;
        }

        Integer min = nums.get(0);
        Integer max = nums.get(0);
        int sum = 0;

        for (Integer x : nums)
        {
            if (x.compareTo(min) < 0) min = x;
            if (x.compareTo(max) > 0) max = x;
            sum += x; // unboxing happens here
        }

        double avg = (double) sum / nums.size();

        System.out.println("Valid numbers: " + nums);
        System.out.println("Min: " + min);
        System.out.println("Max: " + max);
        System.out.println("Sum: " + sum);
        System.out.printf("Average: %.2f%n", avg);
    }

    public static void main(String[] args)
    {
        ArrayList<String> list = new ArrayList<>();
        list.add("10");
        list.add("20");
        list.add("abc");
        list.add("40");
        list.add("-5");
        list.add("200");
        list.add("100");

        ArrayList<Integer> validNums = parseValidIntegers(list);
        printAnalysis(validNums);
    }
}
