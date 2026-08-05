int sumOfEvens(List<int> numbers) {
  int SumEven = 0;
  for (int i = 0; i < numbers.length; ++i) {
    if (numbers[i] % 2 == 0) {
      SumEven += numbers[i];
    }
  }
  return SumEven;
}

int main() {
  // Test cases
  print(sumOfEvens([1, 2, 3, 4])); // Expected output: 6
  print(sumOfEvens([1, 3, 5])); // Expected output: 0
  print(sumOfEvens([-2, -1, 0, 1, 2])); // Expected output: 0
  return 0;
}
