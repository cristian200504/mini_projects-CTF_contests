import java.util.Scanner;

public class Main
{
    static Scanner input = new Scanner(System.in);
    static void printQuestion(String question, String[] options, int number)
    {
        System.out.println(question);
    }
    static char readAnswer(Scanner input)
    {
        return input.next().charAt(0);
    }
    static boolean checkAnswer(char userAnswer, char correctAnswer)
    {
        if(Character.toUpperCase(userAnswer) == correctAnswer)
        {
            return true;
        }
        else
        {
            return false;
        }
    }
    static void printResults(int correctCount, int totalQuestions)
    {
        System.out.println("===== Results =====");
        System.out.printf("Score: %d/%d%n", correctCount, totalQuestions);
        System.out.printf("Percentage: %.2f%%",((double)correctCount/totalQuestions)*100);
    }
    public static void main(String[] args)
    {
        String[] questions = {
                "What is the size of int in Java?",
                "Which keyword creates a subclass?",
                "Which loop is best when iterations are known?"
        };
        String[][] options = {
                {
                        "A. 2 bytes",
                        "B. 4 bytes",
                        "C. 8 bytes",
                        "D. Depends on OS"
                },
                {
                        "A. this",
                        "B. extends",
                        "C. implements",
                        "D. super"
                },
                {
                        "A. while",
                        "B. do-while",
                        "C. for",
                        "D. foreach"
                }
        };
        char[] answers = {
                'B',
                'B',
                'C'
        };
        int correctAnswer = 0;
        for (int i = 0; i < questions.length; i++)
        {
            printQuestion(questions[i], options[i],i);
            for(int j = 0; j < options[i].length; j++)
            {
                System.out.printf("%s%n",options[i][j]);
            }
            System.out.print("Your answer: ");
            char answer = readAnswer(input);
            if(checkAnswer(answer, answers[i]))
            {
                System.out.println("Correct!");
                correctAnswer++;
            }
            else
            {
                System.out.println("Wrong!");
            }
            System.out.println();
        }
        printResults(correctAnswer, questions.length);
    }
}
