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

![GitHub Workflow Status](https://github.com/radon-project/radon/actions/workflows/ci.yaml/badge.svg "GitHub Workflow Status")
![GitHub license](https://img.shields.io/github/license/radon-project/radon?style=flat "License")
![Total hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Fradon-project%2Fradon&count_bg=%2352B308&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false "Total hits")
[![Discord](https://img.shields.io/discord/1137834560290308306?style=flat&logo=discord&logoColor=%235865F2&label=join&link=https%3A%2F%2Fdiscord.gg%2FnNkQKfcxqa "Discord")](https://discord.com/invite/nNkQKfcxqa)

</div>

Radon is a programming language that is designed to be easy to learn and use. It is a high-level language intended to be used for general purpose programming. It is designed to be easy to learn and use, while still being powerful enough to be used for most tasks. Some of the features of Radon include:

- A simple syntax that is easy to learn and use
- Dynamic typing so that you don't have to worry about types
- Powerful standard library that makes it easy to do common tasks (Development)
- Easy to use package manager that makes it easy to install packages (Future feature)

## Installation

Radon is currently in development state. It is not ready for use yet. But you can still try it out by cloning the repository and running the `radon-project/radon` repository.

```bash
git clone https://github.com/radon-project/radon.git
cd radon

# To run the repl
python radon.py

# To run a .rn file use the -s flag and pass the filename
python radon.py -s <filename>
```

Read the [documentation](https://radon-project.github.io/docs) to learn more about the language.

## Quick Start

Here is a simple example of a Radon program that asks the user for their username and password and then checks if the username is "radon" and the password is "password". If the username and password are correct, it prints "Log in successful", otherwise it prints "Invalid credentials".

```radon
import io

class Network {
    fun __constructor__(username, password) {
        this.username = username
        this.password = password
    }

    fun login() {
        if this.username == "radon" {
            if this.password == "password" {
                print("Log in successful")
            } else {
                print("Invalid credentials")
            }
        } else {
            print("Invalid credentials")
        }
    }
}

var username = input("Enter you username: ")
# Access password securely using get_password
var password = io.Input.get_password("Enter your password: ")

var network = Network(username, password)
network.login()
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

You can also join our [Discord server](https://discord.gg/y2x4CSX7DM) to discuss the language and get help.

## License

We are using GNU General Public License v3.0. You can check the license [here](LICENSE).
