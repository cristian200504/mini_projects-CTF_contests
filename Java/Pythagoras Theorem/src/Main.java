import java.util.Scanner;

public class Main
{
    public static void main(String[] args)
    {
        Scanner input = new Scanner(System.in);
        double a,b,c;
        System.out.print("Enter side a: ");
        a = input.nextDouble();
        System.out.print("Enter side b: ");
        b = input.nextDouble();
        c=Math.pow(a,2)+Math.pow(b,2);
        c = Math.sqrt(c);
        System.out.printf("Hypotenuse: %.2f%n", c);
        input.close();
    }
}
