public class Project implements GradeItem
{
    private final double pointsEarned , totalPoints;
    public Project(double pointsEarned, double totalPoints)
    {
        this.pointsEarned = pointsEarned;
        this.totalPoints = totalPoints;
    }
    @Override
    public double calculateScore()
    {
        return (pointsEarned/totalPoints)*100;
    }
}
