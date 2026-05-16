import java.util.Random;

public class Main
{
    public static void main(String[] args)
    {
        Random rand = new Random();
        GradeItem[] finalGradeItems = {
                new Exam(rand.nextDouble(1,10),10),
                new Project(rand.nextDouble(1,10),10),
                new Participation(rand.nextDouble(1,10))
        };
        for(GradeItem gradeItem : finalGradeItems)
        {
            System.out.printf("%.2f%%%n",gradeItem.calculateScore());
        }
    }
}
