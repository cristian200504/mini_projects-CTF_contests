public class Student
{
    String name;
    static int studentCount;
    public Student(String name)
    {
        this.name = name;
        studentCount++;
    }
    static public int getStudentCount()
    {
        return studentCount;
    }
}
