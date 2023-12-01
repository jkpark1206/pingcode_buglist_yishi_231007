import os
import json

processConfigfile = 'processConfig.json'
confDir = os.path.split(os.path.realpath(__file__))[0]
proConfigPath = os.path.join(confDir,processConfigfile)
def gettester(proConfigPath):
    with open(proConfigPath, 'r', encoding='utf-8') as proconf_file:
        proconf_data = json.load(proconf_file)
    return proconf_data['people']['tester']
testerDict = gettester(proConfigPath)

if __name__=='__main__':
    print(testerDict)