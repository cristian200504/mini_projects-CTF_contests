// Problem: Calculate the Sum of Even Numbers
//
// Specification:
// Write a function called `sumOfEvens` that takes a list of integers as input
// and returns the sum of all even numbers in the list.
//
// Requirements:
// 1. The function should accept a List<int> as parameter.
// 2. It should return an int representing the sum.
// 3. Only even numbers (divisible by 2) should be included in the sum.
// 4. If the list is empty or contains no even numbers, return 0.
// 5. Handle negative even numbers correctly (e.g., -2 is even and should be included).
//
// Examples:
// sumOfEvens([1, 2, 3, 4]) should return 6 (2 + 4)
// sumOfEvens([1, 3, 5]) should return 0 (no even numbers)
// sumOfEvens([-2, -1, 0, 1, 2]) should return 0 (-2 + 0 + 2 = 0)
//
// Constraints:
// - List length: 0 <= length <= 1000
// - Integer values: -1000 <= value <= 1000
//
// Implement the function below:

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
