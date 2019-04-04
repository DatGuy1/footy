# -*- coding: utf-8 -*-
import sportsbot
import re
import requests
import json
import time
import wikitextparser as wtp
from bs4 import BeautifulSoup
from datetime import datetime
from wikitools import *

site = wiki.Wiki()
site.login(sportsbot.username, sportsbot.password)

baseURL = 'https://uk.soccerway.com/a/block_player_career?block_id=page_player' \
          '_1_block_player_career_6&callback_params={"people_id":PLAYID}&action' \
          '=changeTab&params={"type":"THETYPE", "formats":["FORMATS"]}'
tableFinder = re.compile(r'{\|.+?(?=\|})\|}', re.S)

def BuildData(competition, pID, pPage):
    finishURL = ''
    if competition == 'League':
        finishURL = baseURL.replace('FORMATS', 'Domestic league')
    elif competition == 'DomCup':
        finishURL = baseURL.replace('FORMATS', 'Domestic cup", ' \
                                      '"Domestic super cup')
    elif competition == 'IntCup':
        finishURL = baseURL.replace('FORMATS', 'International cup", ' \
                                      '"International super cup')
    elif competition == 'International':
        finishURL = baseURL[:170] + '}'
        finishURL = finishURL.replace('THETYPE', 'International')
    else:
        print('Invalid competition')
        return None

    finishURL = finishURL.replace('THETYPE', 'Club')
    finishURL = finishURL.replace('PLAYID', str(pID))

    responseText = requests.get(finishURL).json()
    htmlTable = FilterResponse(responseText, pID, pPage)
    tableData = [[cell.text for cell in row('td')]
                  for row in BeautifulSoup(htmlTable, 'html.parser')('tr')][1:]
    return tableData

def TableColumns(IntCup, IntDuty):
    if IntDuty:
        return {'ECQ': [2, 3],
                'WCQ': [2, 3]
                }
    elif IntCup:
        return {'PRL': [4, 5],
                'LEC': [8, 9],
                'COS': [12, 13],
                'UEL': [10, 11],
                'FAC': [6, 7],
                'UCL': [10, 11],
                'Total': [14, 15]
                }
    else:
        return {'PRL': [4, 5],
                'LEC': [8, 9],
                'COS': [10, 11],
                'FAC': [6, 7],
                'Total': [12, 13]
                }
                

    
def FilterResponse(responseText, pID, pPage):
    if responseText['commands'][1]['parameters']['params']['people_id'] != str(pID):
        print('ID in request and response do not match. Skipping {}'.format(pPage))
        return None

    contentAnswer = responseText['commands'][0]['parameters']['content']
    if '\"no-data\">' in contentAnswer:
        return None

    scriptStart = contentAnswer.find('<script type')
    if scriptStart == -1:
        print('Couldn\'t find <script> tag. Must be an error.')
        return None

    contentAnswer = contentAnswer[:scriptStart]
    contentAnswer = contentAnswer.replace('\/', '/').replace('\"', '"')
    return contentAnswer

def AddTotals(bigTable, seasAppAdd, seasGoalAdd, tableCols, useRow):
    seasonTotalApp = bigTable.cells(row=useRow,
                                    column=tableCols['Total'][0] - 1)
    seasonTotalGoal = bigTable.cells(row=useRow,
                                     column=tableCols['Total'][1] - 1)
    careerTApp = bigTable.cells(row=useRow + 2,
                                column=tableCols['Total'][0] - 1)
    careerTGoal = bigTable.cells(row=useRow + 2,
                                 column=tableCols['Total'][1] - 1)
    clubTApp = bigTable.cells(row=useRow + 1,
                              column=tableCols['Total'][0] - 1)
    clubTGoal = bigTable.cells(row=useRow + 1,
                               column=tableCols['Total'][1] - 1)


    seasonTotalApp.value = re.sub(r'^\d*', '{}'.format(int(re.search(r'^\d*', seasonTotalApp.value).group()) +
                                                       seasAppAdd), seasonTotalApp.value)
    seasonTotalGoal.value = re.sub(r'^\d*', '{}'.format(int(re.search(r'^\d*', seasonTotalGoal.value).group()) +
                                                        seasGoalAdd), seasonTotalGoal.value)
    careerTApp.value = re.sub(r'^\d*', '{}'.format(int(re.search(r'^\d*', careerTApp.value).group()) +
                                                       seasAppAdd), careerTApp.value)
    careerTGoal.value = re.sub(r'^\d*', '{}'.format(int(re.search(r'^\d*', careerTGoal.value).group()) +
                                                        seasGoalAdd), careerTGoal.value)
    clubTApp.value = re.sub(r'^\d*', '{}'.format(int(re.search(r'^\d*', clubTApp.value).group()) +
                                                       seasAppAdd), clubTApp.value)
    clubTGoal.value = re.sub(r'^\d*', '{}'.format(int(re.search(r'^\d*', clubTGoal.value).group()) +
                                                        seasGoalAdd), clubTGoal.value)

    return bigTable

def ReturnCheck(isInternational, compSeason):
    checkPassed = False
    if isInternational:
        for i in range(5):
            if not checkPassed:
                if str(int(datetime.now().year) + i) in compSeason[0] and not re.search(r'U\d{2}', compSeason[1]):
                    checkPassed = True
    else:
        if str(datetime.now().year) in compSeason[0]:
            checkPassed = True
    return checkPassed

def FetchTable(artName, sectName):
    playerSection = page.Page(site, artName, section = sectName)
    sectionText = playerSection.getWikiText()
    rawTable = tableFinder.search(sectionText).group()
    sectTable = wtp.Table(rawTable)
    return sectTable, rawTable

def SavePage(artName, sectName, oldTable, newTable, dryRun):
    dateNow = datetime.now()
    if dryRun:
        origText = page.Page(site, artName).getWikiText()
        origSave = origText.replace('[[', '[[:') # don't embed
        dryPage = page.Page(site, artName)
        if not dryPage.exists:
            dryPage.edit(text=origSave, summary='Creating page for dry run ' \
                         '([[Wikipedia:Bots/Requests for approval/SportsStatsBot 2|BOT]] ' \
                         '- [[User:SportsStatsBot/footyPlayer/help|Help]])', bot=True)

    articlePage = page.Page(site, artName, section=sectName)
    articleText = articlePage.getWikiText()
        
    saveText = articleText.replace(str(oldTable), str(newTable))
    saveText = re.sub(r'(?P<update>{{updated\|.+?(?=\d))\d* \w* \d*', r'\g<update>{}'.format(dateNow.strftime('%d %B %Y').lstrip('0')), saveText)
    articlePage.edit(text=saveText, summary='Updating {}\'s stats as of {} ' \
                     '([[Wikipedia:Bots/Requests for approval/SportsStatsBot 2|BOT]] ' \
                     '- [[User:SportsStatsBot/footyPlayer/help|Help]])'.format(artName[27:] if dryRun else artName,
                                                                               dateNow.strftime('%d/%m/%Y').lstrip('0').replace('/0', '/')),
                     bot=True)# , skipmd5=True) - skipmd5 was only needed whenever there was an encoding error

def main():    
    configPage = page.Page(site, "User:SportsStatsBot/footystatsconfig")
    configJson = json.loads(configPage.getWikiText())
    print(configJson)
    for playerPage in configJson['run']:
        dryRun = False
            
        playerConfig = configJson['run'][playerPage]
        playerID = playerConfig['ID']
        
        print('Name: {}\nID: {}'.format(playerPage, playerID))
        if playerPage in configJson['dryrun']:
            dryRun = True
            playerPage = 'User:SportsStatsBot/dryRun/' + playerPage
            
        for sectName in playerConfig['sections']:
            print(sectName)
            eligibleComp = ['League', 'DomCup']
            
            bigTable, oldTable = FetchTable(playerPage, sectName)
            wikiTData = bigTable.data()
            tableCols = {}
            
            if len(wikiTData[-3]) == 15:
                eligibleComp.append('IntCup')
                tableCols = TableColumns(True, False)
            elif len(wikiTData[-3]) == 13:
                tableCols = TableColumns(False, False)
                
            if 'international' in sectName.lower():
                tableCols = TableColumns(False, True)
                useRow = len(wikiTData) - 2
                tableData = BuildData('International', playerID, playerPage)
                for compSeason in tableData:
                    if not ReturnCheck(True, compSeason):
                        continue
                    
                    try: # This isn't really to find the correct column. More to check if it's an eligible competition
                        appCell = bigTable.cells(row=useRow,
                                                 column=tableCols[compSeason[2]][0] - 1)
                        goalCell = bigTable.cells(row=useRow,
                                                  column=tableCols[compSeason[2]][1] - 1)
                    except KeyError:
                        print('KeyError {}'.format(compSeason[2]))
                        continue

                    oldAppVal = appCell.value
                    oldGoalVal = goalCell.value
                    oldApp = int(re.search(r'^\d*', oldAppVal).group())
                    oldGoal = int(re.search(r'^\d*', oldGoalVal).group())
                    appCell.value = re.sub(r'^\d*', compSeason[4], oldAppVal)
                    goalCell.value = re.sub(r'^\d*', compSeason[9], oldGoalVal)

                    teamTotalApp = bigTable.cells(row=useRow + 1,
                                                  column=tableCols[compSeason[2]][0] - 1)
                    teamTotalGoal = bigTable.cells(row=useRow + 1,
                                                   column=tableCols[compSeason[2]][1] - 1)
                    teamTotalApp.value = re.sub(r'^\d*',
                                                '{}'.format(int(re.search(r'^\d*', teamTotalApp.value).group()) +
                                                            int(compSeason[4]) - oldApp), teamTotalApp.value)
                    teamTotalGoal.value = re.sub(r'^\d*',
                                                 '{}'.format(int(re.search(r'^\d*', teamTotalGoal.value).group()) +
                                                             int(compSeason[9]) - oldGoal), teamTotalGoal.value)

                if str(bigTable) == oldTable:
                    print('{} has no change, skipping'.format(playerPage))
                    continue
                
                finishTable = bigTable

            else:
                useRow = len(wikiTData) - 3
                seasAppAdd = 0
                seasGoalAdd = 0

                for competition in eligibleComp:
                    tableData = BuildData(competition, playerID, playerPage)
                    for compSeason in tableData:
                        if not ReturnCheck(False, compSeason):
                            continue

                        try:
                            appCell = bigTable.cells(row=useRow,
                                                     column=tableCols[compSeason[2]][0] - 1)
                            goalCell = bigTable.cells(row=useRow,
                                                      column=tableCols[compSeason[2]][1] - 1)
                        except KeyError:
                            print('KeyError {}'.format(compSeason[2]))
                            continue
                        
                        oldAppVal = appCell.value
                        oldGoalVal = goalCell.value
                        oldApp = int(re.search(r'^\d*', oldAppVal).group())
                        oldGoal = int(re.search(r'^\d*', oldGoalVal).group())
                        appCell.value = re.sub(r'^\d*', compSeason[4], oldAppVal)
                        goalCell.value = re.sub(r'^\d*', compSeason[9], oldGoalVal)

                        clubTotalApp = bigTable.cells(row=useRow + 1,
                                                      column=tableCols[compSeason[2]][0] - 1)
                        clubTotalGoal = bigTable.cells(row=useRow + 1,
                                                       column=tableCols[compSeason[2]][1] - 1)
                        clubTotalApp.value = re.sub(r'^\d*',
                                                    '{}'.format(int(re.search(r'^\d*', clubTotalApp.value).group()) +
                                                                int(compSeason[4]) - oldApp), clubTotalApp.value)
                        clubTotalGoal.value = re.sub(r'^\d*',
                                                     '{}'.format(int(re.search(r'^\d*', clubTotalGoal.value).group()) +
                                                                 int(compSeason[9]) - oldGoal), clubTotalGoal.value)
                        
                        careerTotalApp = bigTable.cells(row=useRow + 2,
                                                        column=tableCols[compSeason[2]][0] - 1)
                        careerTotalGoal = bigTable.cells(row=useRow + 2,
                                                         column=tableCols[compSeason[2]][1] - 1)
                        careerTotalApp.value = re.sub(r'^\d*',
                                                      '{}'.format(int(re.search(r'^\d*', careerTotalApp.value).group()) +
                                                                  int(compSeason[4]) - oldApp), careerTotalApp.value)
                        careerTotalGoal.value = re.sub(r'^\d*',
                                                       '{}'.format(int(re.search(r'^\d*', careerTotalGoal.value).group()) +
                                                                   int(compSeason[9]) - oldGoal), careerTotalGoal.value)

                        seasAppAdd += int(compSeason[4]) - oldApp
                        seasGoalAdd += int(compSeason[9]) - oldGoal

                if str(bigTable) == oldTable:
                    print('{} has no change, skipping'.format(playerPage))
                    continue

                finishTable = AddTotals(bigTable, seasAppAdd, seasGoalAdd, tableCols, useRow)

            SavePage(playerPage, sectName, oldTable, finishTable, dryRun)

if __name__ == '__main__':
    main()
