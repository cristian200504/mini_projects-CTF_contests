public abstract class DeliveryVehicle
{
    String id;
    public DeliveryVehicle(String id)
    {
        this.id = id;
    }
    abstract void deliver();
    public void showId()
    {
        System.out.println("ID: " + id);
    }
}
