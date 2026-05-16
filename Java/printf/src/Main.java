import java.util.*;
public class Main
{
    public static void main(String[] args)
    {
        Scanner sc = new Scanner(System.in);
        List<Item> items = new ArrayList<>();

        int x = 1;
        while (x == 1)
        {
            Item it = new Item();

            System.out.println("Creating an item...");
            System.out.print("Item name: ");
            it.item = sc.nextLine();

            System.out.print("Item price: ");
            it.price = sc.nextDouble();

            System.out.print("Item quantity: ");
            it.qty = sc.nextInt();

            items.add(it);

            System.out.print("Next item?(1 for yes , 0 for no): ");
            x = sc.nextInt();
            sc.nextLine();
        }

        System.out.printf("%-10s %8s %6s %8s%n", "Item", "Price", "Qty", "Total");
        for (Item it : items) {
            System.out.printf(
                    "%-10s %8.2f %6d %8.2f%n",
                    it.item,
                    it.price,
                    it.qty,
                    it.price * it.qty
            );
        }
        sc.close();
    }
}
