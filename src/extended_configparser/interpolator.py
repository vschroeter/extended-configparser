import configparser
import os

class EnvInterpolation(configparser.ExtendedInterpolation):
    """
    Interpolation which combines ExtendedInterpolation with environment variables interpolation.
    Environment variables in values can be denoted as `${ENV_VAR}` or `$ENV_VAR`. 
    """
    def before_read(self, parser, section, option, value):
        value = super().before_read(parser, section, option, value)
        return os.path.expandvars(value)
