public class Project implements Gradable
{
    private final double score;

    public Project(double score)
    {
        this.score = score;
    }

    @Override
    public double calculateGrade()
    {
        System.out.printf("Project grade: %.2f%n",score);
        return score * 0.3;
    }
}
