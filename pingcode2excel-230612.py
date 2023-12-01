# 2022-12-07 增加“解决方案”，对解决方案为“转需求”的不统计开发缺陷，对解决方案为“重复”的不统计测试缺陷
# 2023-06-12 缩减配置文件内容，增加实际关闭缺陷时间列

import requests
import configparser
import os
import math
import time
import json
import pandas as pd
from functools import partial

headers = {"Content-Type":"application/json"}

def gettoken(id, secret):
    print(id, secret)
    url_token = 'https://open.pingcode.com/v1/auth/token'
    params_token = {'grant_type':'client_credentials','client_id':id,'client_secret':secret}
    res_token = requests.get(url_token, params = params_token)
    token = res_token.json()['access_token']
    return token

def getdeveloper(proConfigPath):
    with open(proConfigPath, 'r', encoding='utf-8') as proconf_file:
        proconf_data = json.load(proconf_file)
    return proconf_data['people']['developer']

def gettester(proConfigPath):
    with open(proConfigPath, 'r', encoding='utf-8') as proconf_file:
        proconf_data = json.load(proconf_file)
    return proconf_data['people']['tester']

def getdevscore(proConfigPath):
    with open(proConfigPath, 'r', encoding='utf-8') as proconf_file:
        proconf_data = json.load(proconf_file)
    return proconf_data['scores']

def getprojectlist(token):
    url_prolist = 'https://open.pingcode.com/v1/project/projects'
    headers["Authorization"] = "Bearer {}".format(token)
    res_prolist = requests.get(url_prolist, headers = headers)
    all_project = res_prolist.json()
    proList=[]
    for i in all_project["values"]:
        tmpdict={}
        tmpdict['id']=i["id"]
        tmpdict['name']=i["name"]
        proList.append(tmpdict)
    return proList

def getseverity(token):
    url_prop = "https://open.pingcode.com/v1/project/properties/severity"
    headers["Authorization"] = "Bearer {}".format(token)
    severity =  requests.get(url = url_prop, headers = headers)
    severityList = severity.json()["options"]
    severityDict = {}
    for i in severityList:
        severityDict[i["_id"]] = i["text"]
    return severityDict

def getsolution(token):
    url_prop = "https://open.pingcode.com/v1/project/properties/solution"
    headers["Authorization"] = "Bearer {}".format(token)
    solution =  requests.get(url = url_prop, headers = headers)
    solutionList = solution.json()["options"]
    solutionDict = {}
    for i in solutionList:
        solutionDict[i["_id"]] = i["text"]
    return solutionDict

def getprojbug(project, severityDict, solutionDict, startstamp, endstamp, token):
    projectid = project['id']
    projectname = project['name']
    url_bug = "https://open.pingcode.com/v1/project/work_items"
    headers["Authorization"] = "Bearer {}".format(token)
    params_bug = {'project_id':projectid,'type':'bug','created_start_at':startstamp,'created_end_at':endstamp}
    res_bug =  requests.get(url = url_bug, params = params_bug, headers = headers)
    total = res_bug.json()['total']
    runtime = math.ceil(total/30)
    buglist = []
    for i in range(runtime):
        params_tmp = {'project_id':projectid, 'type':'bug','created_start_at':startstamp,'created_end_at':endstamp, 'page_index':i}
        tmpbug = requests.get(url = url_bug, params = params_tmp, headers = headers)
        for data in tmpbug.json()['values']:
            tmplist = []
            if data["properties"]["severity"] is None:
                tmpseverity = "未定义"
            else:
                tmpseverity = severityDict[data["properties"]["severity"]]
            if data["properties"]["solution"] is None:
                tmpsolution = "未定义"
            else:
                tmpsolution = solutionDict[data["properties"]["solution"]]
            if data["assignee"] == None:
                tmpassignee = "未定义"
            else:
                tmpassignee = data["assignee"]["display_name"]
            if data["completed_at"] == None:
                tmpcomplete = ""
                tmpaddcomplete = datetoformate(endstamp)
                tmpclose = (endstamp-data["created_at"])/86400
            else:
                tmpcomplete = datetoformate(data["completed_at"])
                tmpaddcomplete = datetoformate(data["completed_at"])
                tmpclose = (data["completed_at"]-data["created_at"])/86400
            tmpcreate = datetoformate(data["created_at"])
            tmplist = [projectname,data["version"]["name"],data['identifier'],data["title"],data["state"]["name"],tmpseverity,tmpsolution,
            tmpassignee,data["created_by"]["display_name"],tmpcreate,tmpcomplete,tmpaddcomplete,tmpclose]
            buglist.append(tmplist)
    return buglist

def datetoformate(timestamp):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

def datetostamp(date):
    return int(time.mktime(time.strptime(date, '%Y-%m-%d %H:%M:%S')))

def devResult(developerDict, scoresDict, df, filename):
    tmpScoreList = []
    df = df.drop (df [df ['解决方案'] == '转需求' ].index)
    df.to_csv ('deve.csv',sep= ',' ,index= False ,header= True, encoding='utf_8_sig')
    for leader in developerDict.keys():
        lp0 = lp1 = lp2 = 0
        lp0t = lp1t = lp2t = 0
        lp0rate = lp1rate = lp2rate = 0
        lp0prerate = lp1prerate= lp2prerate = 0
        for name in developerDict[leader]:
            # print(name)            
            data = df[df['责任人']==name]['严重程度'].value_counts().to_dict()
            if '致命' in data.keys():
                p0 = data['致命']
                p0t = float(df[(df['责任人']==name) & (df['严重程度']=='致命')]['修复时长(天)'].max())
                p0rate = p0t/scoresDict['dtime']['p0']
                p0prerate = 1 - p0rate
                lp0 += p0
                lp0t = max(lp0t, p0t)
                lp0rate = max(lp0rate, p0rate)
            else:
                p0 = 0
                p0t = 0
                p0rate =0
                p0prerate =0
                lp0t = max(lp0t, p0t)
                lp0rate = max(lp0rate, p0rate)
            if '严重' in data.keys():
                p1 = data['严重']
                p1t = float(df[(df['责任人']==name) & (df['严重程度']=='严重')]['修复时长(天)'].max())
                p1rate = p1t/scoresDict['dtime']['p1']
                p1prerate = 1 - p1rate
                lp1 += p1
                lp1t = max(lp1t, p1t)
                lp1rate = max(lp1rate, p1rate)
            else:
                p1 = 0
                p1t = 0
                p1rate =0
                p1prerate =0
                lp1t = max(lp1t, p1t)
                lp1rate = max(lp1rate, p1rate)
            if '一般' in data.keys():
                p2 = data['一般']
                p2t = float(df[(df['责任人']==name) & (df['严重程度']=='一般')]['修复时长(天)'].max())
                p2rate = p2t/scoresDict['dtime']['p2']
                p2prerate = 1 - p2rate
                lp2 += p2
                lp2t = max(lp2t, p2t)
                lp2rate = max(lp2rate, p2rate)
            else:
                p2 = 0
                p2t = 0
                p2rate =0
                p2prerate =0
                lp2t = max(lp2t, p2t)
                lp2rate = max(lp2rate, p2rate)
            score = - (p0*scoresDict['dscores']['p0'] + p1*scoresDict['dscores']['p1'] + p2*scoresDict['dscores']['p2'])
            totalscore = 120 + score
            maxrate = max(p0rate,p1rate,p2rate)
            if maxrate!=0:
                maxprerate = 1-maxrate
            else:
                maxprerate = 0
            tmplist = [name,'组员',p0,p1,p2,score,totalscore,
            p0t,'{:.2%}'.format(p0rate),'{:.2%}'.format(p0prerate),
            p1t,'{:.2%}'.format(p1rate),'{:.2%}'.format(p1prerate),
            p2t,'{:.2%}'.format(p2rate),'{:.2%}'.format(p2prerate),'{:.2%}'.format(maxprerate)]
            if name == leader:
                pass
            else:
                tmpScoreList.append(tmplist)
        if leader == '其他':
            pass
        else:
            lscore= - (lp0*scoresDict['dlscores']['p0'] + lp1*scoresDict['dlscores']['p1'] + lp2*scoresDict['dlscores']['p2'])
            ltotalscore = 120 + lscore

            if lp0rate!=0:
                lp0prerate = 1-lp0rate
            if lp1rate!=0:
                lp1prerate = 1-lp1rate
            if lp2rate!=0:
                lp2prerate = 1-lp2rate
            lmaxrate = max(lp0rate,lp1rate,lp2rate)
            if lmaxrate!=0:
                lmaxprerate = 1-lmaxrate
            else:
                lmaxprerate = 0
            # tmplist = [leader,'组长',lp0,lp1,lp2,lscore,ltotalscore,
            # lp0t,'{:.2%}'.format(lp0rate),'{:.2%}'.format(lp0prerate),
            # lp1t,'{:.2%}'.format(lp1rate),'{:.2%}'.format(lp1prerate),
            # lp2t,'{:.2%}'.format(lp2rate),'{:.2%}'.format(lp2prerate),'{:.2%}'.format(lmaxprerate)]
            # tmpScoreList.append(tmplist)
    tmptitle = [
        "姓名","角色","p0数","p1数","p2数","缺陷扣分","最终得分",
        "p0最长修复时间","p0修复率","p0提前修复率",
        "p1最长修复时间","p1修复率","p1提前修复率",
        "p2最长修复时间","p2修复率","p2提前修复率","Max提前修复率"]
    developerdf = pd.DataFrame(tmpScoreList, columns = tmptitle)
    with pd.ExcelWriter(filename, engine='openpyxl', mode='a') as writer:
       developerdf.to_excel(writer, sheet_name='developer', index = False)

def Result(testerDict, scoresDict, df, filename):
    tmpScoreList = []
    df = df.drop (df [df ['解决方案'] == '误报'].index)
    df.to_csv ('test.csv',sep= ',' ,index= False ,header= True, encoding='utf_8_sig')
    for leader in testerDict.keys():
        lp0 = lp1 = lp2 = 999
        for name in testerDict[leader]:
            data = df[(df['提交人']==name) & (df['当前状态']!='已拒绝')]['严重程度'].value_counts().to_dict()
            # print(data)
            p0 = p1= p2 =0
            if '致命' in data.keys():
                p0 = data['致命']
                # tmplist = p0
                lp0 = min(lp0, p0)
            else:
                p0 = 0
                lp0 = min(lp0, p0)
            if '严重' in data.keys():
                p1 = data['严重']
                lp1 = min(lp1, p1)
            else:
                p1 = 0
                lp1 = min(lp1, p1)
            if '一般' in data.keys():
                p2 = data['一般']
                lp2 = min(lp2, p2)
            else:
                p2 = 0     
                lp2 = min(lp2, p2)       
            score = p0*scoresDict['tscores']['p0'] + p1*scoresDict['tscores']['p1'] + p2*scoresDict['tscores']['p2']
            totlescore = 0 + score
            tmplist = [name,'组员',p0,p1,p2,score,totlescore]
            if name == leader:
                pass
            else:
                tmpScoreList.append(tmplist)
        lscore = lp0*scoresDict['tscores']['p0'] + lp1*scoresDict['tscores']['p1'] + lp2*scoresDict['tscores']['p2']
        ltotalscore = 0 + lscore
        tmplist = [leader,'组长',lp0,lp1,lp2,lscore,ltotalscore]
        tmpScoreList.append(tmplist)
    tmptitle = ["姓名","角色","p0","p1","p2","缺陷分","最终得分"]
    testerdf = pd.DataFrame(tmpScoreList, columns = tmptitle)
    with pd.ExcelWriter(filename, engine='openpyxl', mode='a') as writer:
       testerdf.to_excel(writer, sheet_name='tester', index = False)

def main():
    now = int(time.time())
    
    #转换为其他日期格式,如:"%Y-%m-%d %H:%M:%S"
    timeArray = time.localtime(now)
    timeflag = time.strftime("%Y%m%d%H%M%S", timeArray)
    print(timeflag)
    filename ="pingcode-"+timeflag+".xlsx"

    # 配置相关信息
    confFile = 'config-230612.ini'   #项目相关配置，包括不限于登录系统的账号密码、要统计版本的提测和发布时间
    confDir = os.path.split(os.path.realpath(__file__))[0]
    configPath = os.path.join(confDir, confFile)
    con = configparser.ConfigParser()
    con.read(configPath, encoding='utf-8')
    clDict = {'id':con.get("client", "id"), 'secret':con.get("client", "secret")}   # 登录系统的账号信息
    dlineDict = {'teststart':con.get("default_time", "teststart"), 'testend':con.get("default_time", "testend")}    # 获取项目区间段的数据
    projIdlist = con.sections()[2:]   # 前两个元素不是项目id，只保留后面的列表

    token = gettoken(clDict['id'], clDict['secret'])
    proList = getprojectlist(token)
    severityDict = getseverity(token)
    solutionDict = getsolution(token)

    coltitle = ['项目','版本','缺陷编号','简要描述','当前状态','严重程度','解决方案','责任人','提交人','创建时间','关闭时间','关闭时间（补时）','修复时长(天)']
    tmpBugList = []
    for project in proList:
        projbuglist = []
        if project['id'] in projIdlist:
            projbuglist = getprojbug(project, severityDict,solutionDict,datetostamp(dlineDict['teststart']),datetostamp(dlineDict['testend']),token)
        if not projbuglist:
            pass
        else:
            tmpBugList += projbuglist
    df = pd.DataFrame(tmpBugList, columns = coltitle)
    df['修复时长(天)'].replace("",0,regex=True,inplace=True)
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='buglist', index = False)

    processConfigfile = 'processConfig.json'    #和绩效相关配置，包括不限于每个级别缺陷的扣分加分值、计划修复时间、人员职级和组成
    proConfigPath = os.path.join(confDir,processConfigfile)

    developerDict = getdeveloper(proConfigPath)
    testerDict = gettester(proConfigPath)
    scoresDict = getdevscore(proConfigPath)

    devResult(developerDict, scoresDict, df, filename)
    Result(testerDict, scoresDict, df, filename)

if __name__=='__main__':
    main()