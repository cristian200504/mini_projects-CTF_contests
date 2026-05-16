public class Main
{
    public static void main(String[] args)
    {
        Runnable taskA = new CountingTask("Task A");
        Runnable taskB = new CountingTask("Task B");

        Thread threadA = new Thread(taskA);
        Thread threadB = new Thread(taskB);

        threadA.start();
        threadB.start();
    }
}
