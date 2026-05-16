public class Drone extends DeliveryVehicle
{
    public Drone(String id)
    {
        super(id);
    }
    public void showId(String id)
    {
        super.showId();
    }
    @Override
    public void deliver()
    {
        System.out.println("Drone delivering package");
    }
}
