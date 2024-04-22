

from extended_configparser.configuration.configuration import Configuration
from extended_configparser.configuration.entries import ConfigEntryCollection, ConfigSection


class MainConfigPaths(ConfigEntryCollection):
    def __init__(self) -> None:
        section = ConfigSection("Dirs")
        self.data_root_dir = section.ConfigOption("data_root_dir", r"${HOME}/test/", 
                                                  "Root directory for all data", 
                                                  long_instruction="This is a longer description of what you have to do.")
        
        subdir_section = ConfigSection("Subdirs")
        self.sub_dir = subdir_section.ConfigOption("sub_dir", r"${Dirs:data_root_dir}/subdir/", "Main subdirectory.")


class MainConfig(Configuration):
    def __init__(self) -> None:
        super().__init__("./test_config.cfg")
        self.paths = MainConfigPaths()


config = MainConfig()
config.load()

config.inquire()
