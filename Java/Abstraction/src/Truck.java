public class Truck extends DeliveryVehicle
{
    public  Truck(String id)
    {
        super(id);
    }
    public void showId(String id)
    {
        super.showId();
    }
    @Override
    void deliver()
    {
        System.out.println("Truck delivering cargo");
    }
}
