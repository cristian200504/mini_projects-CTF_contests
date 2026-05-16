public class Car
{
    private final String licensePlate, color;
    private boolean isParked = true;

    public Car(String licensePlate, String color)
    {
        this.licensePlate = licensePlate;
        this.color = color;
    }
    public void leave()
    {
        isParked = false;
    }
    void display()
    {
        if(isParked)
        {
            System.out.printf("License: %s | Color: %s | Parked: true%n", licensePlate, color);
        }
    }
}
