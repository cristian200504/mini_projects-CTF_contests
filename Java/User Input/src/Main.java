import java.util.Scanner;

public class Main
{
    public static void main(String[] args)
    {
        int i=0;
        String password = "java123",type=" ";
        Scanner input = new Scanner(System.in);
        while(i<3)
        {
            System.out.print("Enter password: ");
            type = input.nextLine();
            if (type.equals(password)) {
                System.out.println("Access granted");
                break;
            } else {
                System.out.println("Incorrect password");
            }
            ++i;
        }
        if(i==3 && !type.equals(password))
        {
            System.out.println("Access denied");
        }
        input.close();
    }
}
