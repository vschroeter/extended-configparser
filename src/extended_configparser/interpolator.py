import configparser
import os

class EnvInterpolation(configparser.ExtendedInterpolation):
    """Interpolation which expands environment variables in values."""
    def before_read(self, parser, section, option, value):
        value = super().before_read(parser, section, option, value)
        return os.path.expandvars(value)
