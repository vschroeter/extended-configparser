# Extended Configparser

Extended features for the normal [Python Configparser](https://docs.python.org/3/library/configparser.html):
- Write comments to the configuration file
- Read comments from the configuration file
- Environment variable interpolation inside the configuration file

Furthermore it adds some helper classes to create configuration files interactively by asking the user for input, using the [InquirerPy](https://inquirerpy.readthedocs.io/en/latest/) package.



Inspired by [commented-configparser](https://github.com/Preocts/commented-configparser)



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
