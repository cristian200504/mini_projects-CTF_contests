import java.util.Scanner;

public class Main {
    public static void main(String[] args) {

        Scanner sc = new Scanner(System.in);

        System.out.print("Enter email: ");
        String email = sc.nextLine().trim();
        int domain=0;
        for(int i=0; i<email.length(); i++)
        {
            if(email.charAt(i)=='@')
            {
                domain = i;
                break;
            }
        }
        if(domain == 0)
        {
            System.out.println("Invalid email");
            return;
        }
        System.out.printf("Username: %s%n",email.substring(0,domain));
        System.out.printf("Domain: %s%n",email.substring(domain+1,email.length()));
        System.out.printf("Length: %s%n",email.length());
        sc.close();
    }
}
