public class Exam implements GradeItem
{
    private final double score , maxScore;
    public Exam(double score, double maxScore)
    {
        this.score = score;
        this.maxScore = maxScore;
    }
    @Override
    public double calculateScore()
    {
        return (score/maxScore)*100;
    }
}
