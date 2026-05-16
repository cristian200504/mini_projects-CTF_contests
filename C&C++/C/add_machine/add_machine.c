#include <stdio.h>

int add2(int a,int b)
{
   return a+b;
}

int add3(int a,int b,int c)
{
  return a+b+c;
}

float add2f(float a,float b)
{
  return a+b;
}

int main(void)
{
  int sum2=add2(2,5) , sum3=add3(4,6,2);
  float sum2f=add2f(2.3f,4.2f);

  printf("add2(2,5) equals to %d\n",sum2);
  printf("add3(4,6,2) equals to %d\n",sum3);
  printf("add2f(2.3,4.2) equals to %.2f\n",sum2f);
  return 0;
}

