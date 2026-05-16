public class CountingTask implements Runnable
{
    private final String name;

    public CountingTask(String name)
    {
        this.name = name;
    }

    @Override
    public void run()
    {
        for (int i = 1; i <= 5; i++)
        {
            System.out.println(name + ": " + i);

            try
            {
                Thread.sleep(500);
            }
            catch (InterruptedException e)
            {
                System.out.println(name + " interrupted");
                return;
            }
        }
    }
}
