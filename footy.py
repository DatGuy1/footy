import urllib2, urllib
from wikitools import *
import sportsbot
import re
import os
import json
import time

site = wiki.Wiki()
site.login(sportsbot.username, sportsbot.password)
configpage = page.Page(site, "User:SportsStatsBot/footyconfig")

configorig = configpage.getWikiText()
config = json.loads(configorig)

def main():
    for league in config['run']:
        #if league == "dryrun":
        #    continue
        if (config['run'][league]): # or (config['run']['dryrun'][league])
            try:
                leagueregex = config['leagues'][league]['regex']
            except:
                continue
        else:
            continue
        shortteams = config['leagues'][league]['short']
        urlopen = urllib2.urlopen(config['leagues'][league]['url'])
        new_length = str(len(urlopen.read()))
        txtfiledir = os.path.dirname(os.path.abspath(__file__))+"\\"+league+".txt"
        if not os.path.isfile(txtfiledir):
            f = open(txtfiledir, "w")
            f.write(new_length)
            f.close()
            old_length = 0
        else:
            f = open(txtfiledir, "r")
            old_length = f.read()
            f.close()
        if old_length != new_length:
            f = open(txtfiledir, "w")
            f.write(new_length)
            f.close()
        else:
            if not config['run']['dryrun'][league]:
                continue
        openurl = urllib.urlopen(config['leagues'][league]['url']).read()
        tasks = ['name', 'played', 'won', 'drawn', 'lost', 'for', 'against', 'gd', 'pts']
        for team in config['leagues'][league]['short']:
            for num in range(9):
                everything = re.findall(leagueregex[tasks[num]], openurl)
                everything = [x for x in everything if x != '']
                if num == 0:
                    name = everything
                elif num == 1:
                    played = everything
                elif num == 2:
                    won = everything
                elif num == 3:
                    drawn = everything
                elif num == 4:
                    lost = everything
                elif num == 5:
                    forg = everything
                elif num == 6:
                    against = everything
                elif num == 7:
                    gd = everything
                elif num == 8:
                    pts = everything

        num = 0
        drypage = page.Page(site, "User:SportsStatsBot/dryrun/"+league)
        template = page.Page(site, config['leagues'][league]['template'])
        if config['run']['dryrun'][league]:
            newtext = drypage.getWikiText()
        else:
            newtext = template.getWikiText()

        newtext = newtext.decode('utf8')
        oldtext = newtext

        for team, short in shortteams.iteritems():
            shortname = shortteams[name[num].decode('utf8')]
            newtext = re.sub("team"+str(num+1)+"=\w{3}", "team"+str(num+1)+"="+shortname, newtext, 1)
            newtext = re.sub("win_"+shortname+"=\d*", "win_"+shortname+"="+won[num], newtext, 1)
            newtext = re.sub("draw_"+shortname+"=\d*", "draw_"+shortname+"="+drawn[num], newtext, 1)
            newtext = re.sub("loss_"+shortname+"=\d*", "loss_"+shortname+"="+lost[num], newtext, 1)
            newtext = re.sub("gf_"+shortname+"=\d*", "gf_"+shortname+"="+forg[num], newtext, 1)
            newtext = re.sub("ga_"+shortname+"=\d*", "ga_"+shortname+"="+against[num], newtext, 1)
            num += 1
        if newtext == oldtext:
           continue

        newtext = re.sub("update=.*$", "update={{subst:CURRENTDAY}} {{subst:CURRENTMONTHNAME}} {{subst:CURRENTYEAR}}", newtext, flags=re.MULTILINE)

        if config['run']['dryrun'][league]:
            newtext = re.sub("\[\[Category:[^\]]*]]", "", newtext)
            drypage.edit(text=newtext.encode('utf8'), summary="Bot dry run: Updating football league template ([[User:SportsStatsBot/footyconfig|disable]])")
        else:
            template.edit(text=newtext.encode('utf8'), summary="Bot: Updating football league template ([[User:SportsStatsBot/footyconfig|disable]])")

if __name__ == "__main__":
    main()
# Run speed debugging
#start_time = time.time()
#main()
#print("--- %s seconds ---" % (time.time() - start_time))
