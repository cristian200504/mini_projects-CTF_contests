import java.util.Scanner;

public class Main {
    public static void main(String[] args) {

        Scanner input = new Scanner(System.in);

        System.out.print("What item are you buying? ");
        String item = input.nextLine();

        System.out.print("What is the price? ");
        double price = input.nextDouble();

        System.out.print("How many are you buying? ");
        int quantity = input.nextInt();

        System.out.println("\n--- RECEIPT ---");
        System.out.printf("Item: %s%n", item);
        System.out.printf("Price: $%.2f%n", price);
        System.out.printf("Quantity: %d%n", quantity);
        System.out.printf("Total: $%.2f%n", price * quantity);

        input.close();
    }
}