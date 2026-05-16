public class Participation implements Gradable
{
    private final double score;

    public Participation(double score)
    {
        this.score = score;
    }

    @Override
    public double calculateGrade()
    {
        System.out.printf("Participation grade: %.2f%n",score);
        return score * 0.2;
    }
}
