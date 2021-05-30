from ruamel import yaml
import os
import sys

CFG_FL_NAME = "config.yml"
USER_CFG_SECTION = "Newegg"


class Config:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    def __init__(self):
        # Init config
        
        if not os.path.exists(CFG_FL_NAME):
            print(f"No configuration file {CFG_FL_NAME} found!")
            return
        else:
            self.config = yaml.safe_load(open(CFG_FL_NAME))
        self.save()
        
        
    def save(self):
        with open(CFG_FL_NAME, 'w') as f:
            yaml.dump(self.config, f)