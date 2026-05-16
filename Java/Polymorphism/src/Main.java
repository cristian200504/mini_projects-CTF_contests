import java.util.Random;

public class Main
{
	public static void main(String[] args)
	{
        Random rand = new Random();
        Gradable[] finalGrade = {
                new Participation(rand.nextDouble(1,10)),
                new Project(rand.nextDouble(1,10)),
                new Exam(rand.nextDouble(1,10))
        };
        double sum = 0;
        for(Gradable g : finalGrade)
        {
            sum+=g.calculateGrade();
        }
        System.out.printf("Final grade: %.2f%n",sum);
	}
}
