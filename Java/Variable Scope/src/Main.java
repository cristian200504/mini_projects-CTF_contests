public class Main
{
    static int x = 10;

    static void methodA()
    {
        int x = 5;
        System.out.println(x);
    }

    static void methodB()
    {
        System.out.println(x);
    }

    public static void main(String[] args) {
        methodA();
        methodB();

        //if (true) {
            int y = 20;
        //}

        System.out.println(y);
    }
}
