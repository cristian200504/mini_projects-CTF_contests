public class Participation implements GradeItem
{
    private final double attendedSessions;
    public Participation(double attendedSessions)
    {
        this.attendedSessions = attendedSessions;
    }
    @Override
    public double calculateScore()
    {
        return (attendedSessions/10)*100;
    }
}
