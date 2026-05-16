import java.util.Scanner;

public class Main
{
    public static void main(String[] args)
    {
        Scanner sc = new Scanner(System.in);

        System.out.print("Enter filename (example report_2025.pdf): ");
        String file = sc.nextLine().trim();

        int us = file.indexOf('_');
        int dot = file.lastIndexOf('.');

        if (us <= 0 || dot <= us + 1 || dot == file.length() - 1)
        {
            System.out.println("Invalid filename");
            sc.close();
            return;
        }
        System.out.printf("Base name: %s%n",file.substring(0,us));
        System.out.printf("Year: %s%n",file.substring(us + 1,dot));
        System.out.printf("Extension: %s%n",file.substring(dot + 1));
        sc.close();
    }
}
