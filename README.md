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
```

... or directly from GitHub:
```bash
pip install extended-configparser@git+https://github.com/vschroeter/extended-configparser
```

## Example Usage

```python 
from extended_configparser.parser import ExtendedConfigParser

# Load the config
config = ExtendedConfigParser()
config.read("myconfig.cfg")

# Use the configuration as usual
...

# Update the configuration as usual
...

# Access and alter the comments of a section or an option
comment = config.get_comment("Section1")
parser.set_comment("Section.A", comment = "New Section Comment")
parser.set_comment("Section.A", "option1", comment = "New option comment")

# Save the config back to the file
with open("myconfig.cfg", "w") as savefile:
    config.write(savefile)
```

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


## Related projects

This project is snspired by [commented-configparser](https://github.com/Preocts/commented-configparser).
However, it is not a fork, but a new implementation to allow in code manipulation of comments.


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

