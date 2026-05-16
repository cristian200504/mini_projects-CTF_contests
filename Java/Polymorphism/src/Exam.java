public class Exam implements Gradable
{
    private final double score;

    public Exam(double score)
    {
        this.score = score;
    }

    @Override
    public double calculateGrade()
    {
        System.out.printf("Exam grade: %.2f%n",score);
        return score * 0.5;
    }
}
