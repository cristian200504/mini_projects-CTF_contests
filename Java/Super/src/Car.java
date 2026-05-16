public class Car extends Vehicle
{
    String brand;
	public Car(String brand)
	{
        super(brand);
        this.brand = brand;
    }
    void start()
    {
        super.start();
        System.out.println("Car ready to drive");
    }
}
