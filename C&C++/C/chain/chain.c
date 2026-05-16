int multiply (int a , int b)
{
    return a*b;
}
int add(int a,int b)
{
    return a+b;
}
int combo()
{
    int a=2,b=3,c=4,d=5;
    return add(a,b)+multiply(c,d);
}
int main()
{
    return combo();
}
