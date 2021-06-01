from ruamel import yaml
import os
import sys
CFG_FL_NAME = "config.yml"
ROOT = 'bot'
from bot import settings

class Config:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    def __init__(self, path='', custom_path=None):
        # Init config     
        self.path = ROOT   
        if custom_path:
            self.path += f"/{custom_path}"
        else:
            self.path += f"/{path}/config/{CFG_FL_NAME}"
            
        if not os.path.exists(self.path):
            print(f"No configuration file {self.path} found!")
            raise FileNotFoundError
                                         
                                         
    def load(self):
        self.config = yaml.safe_load(open(self.path))
        
    def save(self ,value):
        with open(self.path, 'w') as file:
            yaml.dump(value, file, default_flow_style=False)