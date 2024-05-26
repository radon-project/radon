<div align="center">
<img src="logo.png" height=250>

<h1>The Radon Programming Language</h1>
<p>A general-purpose programming language, focused on simplicity, safety and stability.</p>

[Website](https://radon-project.github.io)
•
[Documentation](https://radon-project.github.io/docs)
•
[Tests](tests/)
•
[Examples](examples/)

<a href="https://github.com/radon-project/radon" title="GitHub stars">
  <img src="https://img.shields.io/github/stars/radon-project/radon?style=flat&logo=github" alt="GitHub stars">
</a>
<a href="https://github.com/radon-project/radon" title="GitHub forks">
  <img src="https://img.shields.io/github/forks/radon-project/radon?style=flat&logo=github" alt="GitHub forks">
</a>
<a href="https://github.com/radon-project/radon" title="GitHub watchers">
  <img src="https://img.shields.io/github/watchers/radon-project/radon?style=flat&logo=github" alt="GitHub watchers">
</a>
<a href="https://github.com/radon-project/radon/issues" title="GitHub issues">
  <img src="https://img.shields.io/github/issues/radon-project/radon?style=flat&logo=github" alt="GitHub issues">
</a>
<a href="https://github.com/radon-project/radon/pulls" title="GitHub pull requests">
  <img src="https://img.shields.io/github/issues-pr/radon-project/radon?style=flat&logo=github" alt="GitHub pull requests">
</a>
<a href="https://github.com/radon-project/radon" title="Total hits">
  <img src="https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Fradon-project%2Fradon&count_bg=%2352B308&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false"/>
  <a href="https://discord.gg/y2x4CSX7DM" title="Join the community">
  <img src="https://img.shields.io/discord/1137834560290308306?style=flat&logo=discord&logoColor=%235865F2&label=join&link=https%3A%2F%2Fdiscord.gg%2Fy2x4CSX7DM" alt="Discord">
</a>
</a>
</div>

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
│   ├── builtin_funcs.py
│   ├── datatypes.py
│   ├── errors.py
│   ├── __init__.py
│   ├── interpreter.py
│   ├── lexer.py
│   ├── nodes.py
│   ├── parser.py
│   └── tokens.py
├── examples
│   ├── args_test.rn
│   ├── arrays.rn
│   ├── classes.rn
│   ├── functions.rn
│   ├── import_test.rn
│   ├── new_syntax.rn
│   ├── python_api.rn
│   ├── simple.rn
│   └── syntax.rn
├── logo.png
├── Makefile
├── radon.py
├── README.md
├── stdlib
│   ├── Argparser.rn
│   ├── Array.rn
│   ├── Math.rn
│   ├── String.rn
│   ├── System.rn
│   └── Winlib.rn
├── tests
└── TODO.md
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

# Assignment operators (Development)
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

c = "Hello"
d = "World"
print(c + " " + d) # Hello World

# Conditional statement
if a > b
{
    print("a is greater than b")
}
elif a < b {
    print("a is less than b")
}
else
{
    print("a is equal to b")
}

# For loop
 x = 9 # Multiplication table of 9

for i = 1 to 11 {
    print(str(x) + " X " + str(i) + " = " + str(x * i))
}

# While loop
while x > 0 {
    print(x)
    var x = x - 1
}

# Function definition
fun add(a, b) {
    return a + b
}

print(add(10, 20)) # 30

# Anonymous function
sub = fun (a, b) {
    return a - b
}

print(sub(20, 10)) # 10

# Single line function
fun mul(a, b) -> a * b
print(mul(10, 20)) # 200

# Class definition
class Person {
    # Constructor
    fun __constructor__(name, age) {
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

# Use a class
person = Person("Almas", 21)
details = "Name is : " + person.get_name() + ", Age : " + str(person.get_age())
print(details)

# Import statement
import Math # to include math library
import "examples/simple.rn" # to use a path

# builtin functions

# Utility methods
cls()
clear()
exit()

# same as include statement
require()

# API methods
pyapi(string)

# Typecase methods
int()
float()
str()
bool()
type()

# Type checker methods
is_num()
is_int()
is_float()
is_str()
is_bool()
is_array()
is_fun()

# String methods
str_len()
str_find(string, index)
str_slice(string, start, end)

# I/O methods
print()
print_ret()
input()
input_int()

# Array methods
arr_len()
arr_push(array, item)
arr_pop(array, index)
arr_append(array, item)
arr_extend(array1, array2)
arr_find(array, index)
arr_slice(array, start, end)
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

We are using GNU General Public License v3.0. You can check the license [here](LICENSE).
