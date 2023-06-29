# Radon - A programming language

Radon is a programming language that is designed to be easy to learn and use. It is a high-level language intended to be used for general purpose programming. It is designed to be easy to learn and use, while still being powerful enough to be used for most tasks. Some of the features of Radon include:

- A simple syntax that is easy to learn and use
- Dynamic typing so that you don't have to worry about types
- Powerful standard library that makes it easy to do common tasks (On the way)
- Easy to use package manager that makes it easy to install packages (Future feature)

## Installation

It is currently in development state. It is not ready for use yet. But you can still try it out by cloning the repository and running the `radon-project/radon` repository. 

```bash
git clone https://github.com/radon-project/radon.git
cd radon

# To run the repl
python radon.py

# To run a .rn file use the -s flag and pass the filename
python radon.py -s <filename>
```

## Project Structure

```
radon
├── core
│   ├── errors.py
│   ├── __init__.py
├── examples
│   ├── arrays.rn
│   ├── classes.rn
│   ├── functions.rn
│   ├── import_test.rn
│   ├── new_syntax.rn
│   ├── simple.rn
│   └── syntax.rn
├── Makefile
├── radon.py
├── README.md
├── stdlib
│   ├── Array.rn
│   ├── Math.rn
│   ├── String.rn
│   └── System.rn
└── tests
```

## Standard Library

We are currently working on the standard library. We need contributors to help us build the standard library. If you are interested, please make contributions to the `stdlib` directory.


## Syntax

Check out the syntax:

```radon
# This is a comment

# Arithmetic operators
# + - Addition
# - - Subtraction
# * - Multiplication
# / - Division
# % - Modulus
# ^ - Exponentiation

# Comparison operators
# == - Equal to
# != - Not equal to
# > - Greater than
# < - Less than
# >= - Greater than or equal to
# <= - Less than or equal to

# Logical operators
# and - Logical and
# or - Logical or
# not - Logical not

# Assignment operators (Future feature)
# = - Assign
# += - Add and assign
# -= - Subtract and assign
# *= - Multiply and assign
# /= - Divide and assign
# %= - Modulus and assign
# ^= - Exponentiation and assign

# Variable definition
var a = 10
var b = 20
print(a + b) # 30

var c = "Hello"
var d = "World"
print(c + " " + d) # Hello World

# Conditional statement
if a > b {
    print("a is greater than b")
} 
elif a < b {
    print("a is less than b")
} 
else {
    print("a is equal to b")
}

# For loop
var x = 9 # Multiplication table of 9

for i = 1 to 10 {
    print(x + " X " + i + " = " + x * i)
}

# While loop
while x > 0 {
    print(x)
    x = x - 1
}

# Function definition
fun add(a, b) {
    return a + b
}

print(add(10, 20)) # 30

# Anonymous function
var sub = fun (a, b) {
    return a - b
}

print(sub(20, 10)) # 10

# Single line function
fun mul(a, b) -> a * b
print(mul(10, 20)) # 200

# Class definition
class Person {
    # Constructor
    fun Person(name, age) {
        var this.name = name
        var this.age = age
    }

    fun get_name() {
        return this.name
    }

    fun get_age() {
        return this.age
    }
}

# builtin functions

int()
float()

is_num()
is_str()
is_bool()
is_list()

strlen()
arrlen()

print()
print_ret()
input()
input_int()

push()
pop()
append()
extend()

```

## Contributing

We need contributors to help us build the language. If you are interested, please make contributions to the `radon-project/radon` repository. 

Steps to contribute:

1. Fork the repository
2. Clone the repository
3. Create a new branch
4. Make changes
5. Commit changes
6. Push to the branch
7. Create a pull request

Before making a pull request create an issue and discuss the changes you want to make. If you have any questions, feel free to ask in the issues section.

## License

This project will be licensed soon. We are still deciding on the license. We will update the license as soon as we decide on the license. 

