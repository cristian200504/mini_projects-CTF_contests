import java.util.Scanner;

public class Main
{
    public  static void main(String[] args)
    {
        Scanner input = new Scanner(System.in);
        Engine e = new Engine(300,4);
        Car c= new Car(e);
        System.out.println(c.getEngine().getHorsepower());
        System.out.println(c.getEngine().getFuel()+"L");
        c = null;
        System.out.println(e.getHorsepower());
        System.out.println(e.getFuel()+"L");
    }
}
