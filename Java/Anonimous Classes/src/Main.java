public class Main
{
    public static void main(String[] args)
    {
        Event[] events =
                {
                        new Event()
                        {
                            @Override
                            public void handle()
                            {
                                System.out.println("System booting...");
                                System.out.println("Loading services...");
                                System.out.println("System ready.");
                            }
                        },

                        new Event()
                        {
                            @Override
                            public void handle()
                            {
                                System.out.println("WARNING!");
                                System.out.println("High memory usage detected.");
                            }
                        },

                        new Event()
                        {
                            @Override
                            public void handle()
                            {
                                System.out.println("Shutting down...");
                                System.out.println("Saving state...");
                                System.out.println("Goodbye.");
                            }
                        }
                };

        for (Event event : events)
        {
            System.out.println();
            event.handle();
        }
    }
}
