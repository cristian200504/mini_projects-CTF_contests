public class Main
{
	public static void main(String[] args)
	{
		Car car1=new Car("ABC-123","Red");
		Car car2=new Car("XYZ-999","Blue");
		Car car3=new Car("LMN-456","Black");
        car2.leave();
        car1.display();
        car2.display();
        car3.display();
	}
}
