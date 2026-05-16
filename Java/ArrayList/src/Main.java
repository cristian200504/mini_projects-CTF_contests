import java.util.ArrayList;

public class Main
{
    public static void main(String[] args)
    {
        ArrayList<Integer> nums = new ArrayList<>();
        nums.add(10);
        nums.add(-3);
        nums.add(25);
        nums.add(-1);
        nums.add(0);
        for(int i=0;i<nums.size();i++)
        {
            Integer num = nums.get(i);
            if(nums.get(i) >= 0)
            {
                nums.set(i, num * 2);
                System.out.println(nums.get(i));
            }
            else
            {
                nums.remove(i);
                i--;
            }
        }
    }
}
