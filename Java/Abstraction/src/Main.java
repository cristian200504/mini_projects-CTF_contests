public class Main
{
	public static void main(String[] args)
	{
        Truck truck = new Truck("TR-01");
        Drone drone = new Drone("DR-99");
        truck.showId(truck.id);
        truck.deliver();
        drone.showId(drone.id);
        drone.deliver();
    }
}
