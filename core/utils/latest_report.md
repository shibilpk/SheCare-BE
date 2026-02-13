You can add two numbers in Python in several ways, from the simplest direct addition to taking user input and using functions.

Here are a few common methods:

---

### 1. Simplest Way: Direct Addition

This is the most straightforward method where you define the numbers directly in your code.

```python
# Define two numbers
num1 = 10
num2 = 25

# Add them together
sum_result = num1 + num2

# Print the result
print(f"The sum of {num1} and {num2} is: {sum_result}")
```

---

### 2. Using a Function (Recommended for Reusability)

Encapsulating the addition logic within a function makes your code more organized and reusable.

```python
def add_two_numbers(a, b):
  """
  This function takes two numbers as arguments and returns their sum.
  """
  return a + b

# Example usage:
number1 = 15
number2 = 7

# Call the function
total = add_two_numbers(number1, number2)

print(f"Using a function: The sum of {number1} and {number2} is: {total}")

# You can call it with different numbers as well
print(f"Using a function: The sum of 3.5 and 2.1 is: {add_two_numbers(3.5, 2.1)}")
```

---

### 3. Taking User Input

This method allows the user to enter the numbers at runtime. It's crucial to convert the input (which is always a string) to a numeric type (like `int` or `float`) before performing arithmetic operations.

```python
print("--- Adding Two Numbers from User Input ---")

try:
    # Get the first number from the user
    # input() always returns a string, so convert it to a float
    num1_str = input("Enter the first number: ")
    number1 = float(num1_str) # Use float for decimal numbers, int for whole numbers

    # Get the second number from the user
    num2_str = input("Enter the second number: ")
    number2 = float(num2_str) # Use float for decimal numbers, int for whole numbers

    # Add the numbers
    sum_of_inputs = number1 + number2

    # Print the result
    print(f"The sum of {number1} and {number2} is: {sum_of_inputs}")

except ValueError:
    # Handle cases where the user enters non-numeric input
    print("Invalid input. Please enter valid numbers only.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

print("------------------------------------------")
```

**Explanation of User Input Method:**

*   **`input()`**: This function displays a message to the user and waits for them to type something and press Enter. It always returns the user's input as a **string**.
*   **`float()` (or `int()`):** Since you can't perform mathematical addition on strings (e.g., `"5" + "3"` would result in `"53"`), you need to convert the string input into a number.
    *   `float()` converts the string to a floating-point number (which can have decimals, like 3.14).
    *   `int()` converts the string to an integer (whole number, like 5). Choose `float()` if you want to allow decimal numbers.
*   **`try-except` block**: This is crucial for robust programs. If a user types something that cannot be converted to a number (like "hello"), `float()` (or `int()`) will raise a `ValueError`. The `try-except` block catches this error gracefully, preventing the program from crashing and instead printing a helpful message.

Choose the method that best fits your specific needs. For simple scripts, direct addition is fine. For more complex applications, using functions and handling user input gracefully are best practices.