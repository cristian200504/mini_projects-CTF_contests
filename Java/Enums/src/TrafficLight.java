public enum TrafficLight
{
    RED(30),
    YELLOW(5),
    GREEN(25);

    private final int durationSeconds;

    TrafficLight(int durationSeconds)
    {
        this.durationSeconds = durationSeconds;
    }

    public int getDurationSeconds()
    {
        return durationSeconds;
    }
}
