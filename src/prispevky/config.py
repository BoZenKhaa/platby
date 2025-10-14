import configparser
import os
import importlib.resources as resources


def read_config(config_paths):
    config = configparser.ConfigParser()

    read_configs = config.read(config_paths, encoding='utf-8')
    if read_configs:
        print("Succesfully read config from: {}".format(str(read_configs)))
    else:
        print("Failed to find any config in {}".format([os.path.abspath(path) for path in config_paths]))
    return config


CONFIG_FILEPATH =  resources.files('prispevky.cfg')/'config_prispevky.cfg'
# CONFIG_FILEPATH = './cfg/config_test.cfg'
CONFIG = read_config([CONFIG_FILEPATH,])
