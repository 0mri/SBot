from ruamel import yaml
import os
import sys

CFG_FL_NAME = "config.yml"
USER_CFG_SECTION = "Newegg"


class Config:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    def __init__(self, path):
        # Init config
        
        if not os.path.exists(f"bot/{path}/config/{CFG_FL_NAME}"):
            print(f"No configuration file bot/{path}/config/{CFG_FL_NAME} found!")
            raise FileNotFoundError
        else:
            self.config = yaml.safe_load(open(f"bot/{path}/config/{CFG_FL_NAME}"))
        
    def save(self):
        with open(CFG_FL_NAME, 'w') as f:
            yaml.dump(self.config, f)