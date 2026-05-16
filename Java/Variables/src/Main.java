public class Main
{
    public static void main(String[] args)
    {
        int a = 7;
        int b = a;
        b = 9;

        System.out.println(a);

        Box box1 = new Box();
        box1.value = 3;

        Box box2 = box1;
        box2.value = 8;

        System.out.println(box1.value);
    }
}

class Box
{
    int value;
}
