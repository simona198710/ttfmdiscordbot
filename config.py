import configparser
import os, sys,codecs

application_path = os.path.dirname(__file__)

config = configparser.ConfigParser()

config.read_file(codecs.open(str(application_path)+'/config.ini', "r", "utf8"))

discordtoken = config['SETTINGS']['discordtoken'].strip()
prefix = config['SETTINGS']['prefix'].strip()