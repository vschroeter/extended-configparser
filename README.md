# Extended Configparser

Extended features for the normal [Python Configparser](https://docs.python.org/3/library/configparser.html):
- Write comments to and read comments from the configuration file
- Access and alter the comments of a section or an option in your code
- Environment variable interpolation inside the configuration file

Furthermore it adds some helper classes to create configuration files interactively by asking the user for input, using the [InquirerPy](https://inquirerpy.readthedocs.io/en/latest/) package.

## Installation

From PyPI:

```bash
pip install extended-configparser
# Or if you plan to use the interactive configuration setup
pip install extended-configparser[cli]
```

... or directly from GitHub:
```bash
pip install extended-configparser@git+https://github.com/vschroeter/extended-configparser
```

## Example Usage

```python
from extended_configparser.parser import ExtendedConfigParser

# Load the config
parser = ExtendedConfigParser()
parser.read("myconfig.cfg")

# Use the configuration as usual
...

# Set sections / options together with comments
parser.add_section("Section.New", comment="New Section with a comment")
parser.set("Section.New", "new_option", "new_value", comment="New value with new comment")

# Access and alter the comments of a section or an option
comment = config.get_comment("Section.A")
parser.set_comment("Section.A", comment = "New Section Comment")
parser.set_comment("Section.A", "option1", comment = "New option comment")

# Save the config back to the file
with open("myconfig.cfg", "w") as savefile:
    config.write(savefile)
```

Thus, configuration files with comments stay readable:
```ini
### myconfig.cfg BEFORE ###

# This is the old comment for Section.A
[Section1]
# This is the old comment for option1
option1 = value1
# This is the multiline
# comment for option2
option2 = value1
...

----------------------------------------
### myconfig.cfg AFTER ###

# New Section Comment
[Section1]
# New option comment
option1 = value1
# This is the multiline
# comment for option2
option2 = value1
...
```

> [!IMPORTANT]
> While the comments are preserved, the formatting is not guaranteed to be the same as before.

## Environment Interpolation

```python
import configparser
from extended_configparser.parser import ExtendedConfigParser
from extended_configparser.interpolator import EnvInterpolation

# Normal or extended configparser with EnvInterpolation()
# parser = configparser.ConfigParser(interpolation=EnvInterpolation())
parser = ExtendedConfigParser(interpolation=EnvInterpolation())
parser.read("config.cfg")
```

Using the `EnvInterpolation` environment variables gets substituted:

```ini
# Assuming the following environment variables:
# TEMP_ENV_VAR1 = "temp1"
# TEMP_ENV_VAR2 = "temp2"

[Section1]
a = a
b = ${a}                # -> b = a
c = $TEMP_ENV_VAR1/${b} # -> c = temp1/a
d = ${TEMP_ENV_VAR2}    # -> d = temp2

[Section2]
# -> a = a
a = ${Section1:a}
# -> b = temp1/a/temp2
b = $TEMP_ENV_VAR1/${Section1:b}/${TEMP_ENV_VAR2}
```

## Advanced & Interactive Configuration

### Creating a Configuration Class

For each of your configuration files, you can create a class that inherits from `Configuration` and contains `ConfigEntry` objects.
These objects make the configuration file more readable and usable in code.

```python
class MyConfig(Configuration):
    def __init__(self, path: str):
        super().__init__(path)
        self.value1 = ConfigEntry(
            section="Section1",
            option="value1",
            default="default",
            message="Description of value1"
        )

        self.value2 = ConfigEntry(
            section="Section1",
            option="value2",
            default="default",
            message="Description of value2"
        )

# Create / Load the configuration
config = MyConfig("myconfig.cfg")
config.load()

# Read the config values
print(config.value1)
print(config.value2)

# Set new values
config.value1 = "new value"

# Write the config back
config.write()
```

### Interactive Configuration

Your configuration class can also be used for an interactive configuration setup.
This is useful for the first setup of a configuration file.

> [!NOTE]
> To use the `config.inquire()` method, .you have to install the package in the cli configuration `pip install extended-configparser[cli]`.

```python
config = MyConfig("myconfig.cfg")
# Load the configuration if existing.
config.load()
# Inquire the user for the configuration values
# Each ConfigEntry will be asked for its value
config.inquire()
# Write the config back
config.write()
```

### Further Configuration Definition Options

To define more complex configurations, you can use `ConfigEntryCollection` and `ConfigSection` objects.

Interpolation of environment variables and other section values is supported by default.

```python

# Collection of values used in your configuration
class MainConfigPaths(ConfigEntryCollection):
    def __init__(self):
        # Shortcut to create options on the same section
        section = ConfigSection("Dirs")
        self.data_root_dir = section.Option(
            "data_root_dir",
            r"${HOME}/data/",
            "Root directory for all data",
            is_dir=True, # Access to this value automatically creates the directory
            long_instruction="The subdirectories defined in [Subdirs] will be created in this directory, except you define them as absolute paths.",
        )
        self.app_data_dir = section.Option(
            "app_data_dir",
            r"/opt/app/data/",
            "Directory for application data from the app.",
            is_dir=True, # Access to this value automatically creates the directory
        )

        self.cache_dir = ConfigEntry(
            "Subdirs
            "cache_dir",
            r"${Dirs:data_root_dir}/cache/",
            "Main directory for cache files, e.g. for the discovering process.",
            is_dir=True, # Access to this value automatically creates the directory
        )


class MyConfig(Configuration):
    def __init__(self, path: str):
        super().__init__(path)

        # Automatically inqiure the user a n/Y question
        self.enabled = ConfirmationOption("enabled", True, "Enable something")

        # Normal ConfigEntry
        self.value1 = ConfigEntry(
            section="Section1",
            option="value1",
            default="default",
            message="Description of value1"
            inquire=self.is_enabled, # Only ask for this value if enabled is True
        )

        # Value transformed ConfigEntry
        self.some_number = ConfigEntry(
            "some_number",
            4,
            "A number:",
            inquire=self.is_enabled,
            value_getter=int, # Automatically transforms the string value into an integer
            # Automatically transforms the integer value into a string on write
            value_setter=lambda x: str(x), # The same like 'value_setter=str', which is the default
            long_instruction="This number is a number :D",
        )

        # Include the ConfigEntryCollection
        self.paths = MainConfigPaths()

        # Selection of multiple predefined values
        self.selection = ConfigSelectionEntry(
            section="Test",
            option="a_selection",
            default=["b"],
            message="Test selection entry",
            choices=["a", "b", "c"],
            multiselect=True,
            delimiter=",\n", # Defines how the value is written back and read
        )

config = MyConfig("myconfig.cfg")
config.load()
config.inquire()
config.write()
```

## Dev Setup
```bash
git clone https://github.com/vschroeter/extended-configparser.git && cd extended-configparser
git checkout dev
pip install -e .[dev]
```

## Contributing

Contributions to extend the functionality or to solve existing problems are welcome!
Requirements for pull requests are:
- All code is tested (if applicable). Running `nox` (or `pytest`) should not raise any errors.
- Naming is consistent with project naming.
- `pre-commit` passes all selected pre-commit checks.
- Commits are squashed and contain a clear commit message describing what functionality is added.


## Related projects

This project is inspired by [commented-configparser](https://github.com/Preocts/commented-configparser).
However, it is not a fork, but a new implementation to allow in-code manipulation of comments.

## FAQ

### Why not just using much simpler EnvInterpolation?

Here on [Stackoverflow](https://stackoverflow.com/questions/26586801/configparser-and-string-interpolation-with-env-variable) a much simpler answer is posted:
```python
class EnvInterpolation(configparser.ExtendedInterpolation):
    """
    Interpolation which combines ExtendedInterpolation with environment variables interpolation.
    Environment variables in values can be denoted as `${ENV_VAR}` or `$ENV_VAR`.
    """
    def before_read(self, parser, section, option, value):
        value = super().before_read(parser, section, option, value)
        return os.path.expandvars(value)
```

This solution however does not allow for fetching the raw values in the configuration file.
Especially for writing back, the raw values are needed to keep the correct configuration.

## License
This project is licensed under the Apache License 2.0.
For details, please see the LICENSE file.
By contributing to this project, you agree to abide by the terms and conditions of the Apache License 2.0.
