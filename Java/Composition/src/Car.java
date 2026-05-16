public class Car
{
    private final Engine engine;
    public Car(int horsepower, int fuel)
    {
        this.engine = new Engine(horsepower,fuel);
    }
    public int getEngineHorsepower()
    {
        return engine.getHorsepower();
    }
    public int getEngineFuel()
    {
        return engine.getFuel();
    }
}
