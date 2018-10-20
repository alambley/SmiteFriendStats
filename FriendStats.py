import hirez
import logging
import os
import operator
import sys
import codecs

def StringToTextFile(path,string):
    text_file = open(path, "w")
    text_file.write(string)
    text_file.close()

def TextFileToString(path):
    if os.path.exists(path):
        with open(path, 'r') as myfile:
            data = myfile.read()
        return data

def CalcKD(kill, death, assist):
    # kill += assist *.5
    if kill != 0 and death != 0:
        return kill/death
    elif kill != 0 and death == 0:
        return kill*1.5
    elif kill == 0 and death != 0:
        return (1/2)/death
    else:
        return 1

def GetMatchOutcome(list, id):
    for x in list:
        if x[0] == id:
            return x[1]

class PlayerStat():
    def __init__(self,username):
        self.username = username
        self.numbGames = 0
        self.kills = 0
        self.deaths = 0
        self.KD = 0
        self.assists = 0
        self.bestKill = 0
        self.bestDeath = 0
        self.bestKD = -100
        self.worstKill = 0
        self.worstDeath = 0
        self.worstKD = 100

    def addGame(self, kill, death, assist):
        self.numbGames += 1
        self.kills += kill
        self.deaths += death
        self.assists += assist
        self.KD = CalcKD(self.kills,self.deaths,self.assists)
        if CalcKD(kill,death, assist) > self.bestKD:
            self.bestKD = CalcKD(kill,death,assist)
            self.bestKill = kill
            self.bestDeath = death
        if CalcKD(kill,death,assist) < self.worstKD:
            self.worstKD = CalcKD(kill,death,assist)
            self.worstKill = kill
            self.worstDeath = death

    def __str__(self):
        toReturn = ""
        if self.username != "":
            toReturn += "Username : {0}\n".format(self.username.split("]")[-1])
        else:
            toReturn += "Username : [ProfileBlockedAccounts]\n"
        toReturn += "NumbGames : {0}\n".format(self.numbGames)
        toReturn += "Kills : {0}\n".format(self.kills)
        toReturn += "Deaths : {0}\n".format(self.deaths)
        toReturn += "Assists : {0}\n".format(self.assists)
        toReturn += "KD : {:0.2f}\n".format(self.KD)
        toReturn += "Best Game : {0}-{1} {2:2.2f}\n".format(self.bestKill, self.bestDeath, self.bestKD)
        toReturn += "Worst Game : {0}-{1} {2:2.2f}\n".format(self.worstKill, self.worstDeath, self.worstKD)
        return toReturn


class PlayerStatList():
    def __init__(self):
        self.list = []

    def addPlayerGame(self, player, kill, death, assist):
        found = False
        for x in range(len(self.list)):
            if self.list[x].username == player:
                self.list[x].addGame(kill,death,assist)
                found = True
                break
        if not found:
            self.list.append(PlayerStat(player))
            self.addPlayerGame(player, kill, death, assist)

    def sort(self):
        self.list.sort(key=operator.attrgetter('numbGames'),reverse=True)

def GeneralStats(apiSession, username):
    myMatchHistory = apiSession.APICall("getmatchhistory", username)
    if myMatchHistory[0]["ret_msg"] != None:
        logging.error("Username '{}' has no match history. Check that it is spelled correctly.".format(username))
        sys.exit(-1)
    wins = 0
    losses = 0
    kills = 0
    deaths = 0
    mostKills = 0
    mostDeaths = 0
    bestKD = 0
    worstKD = 0
    surrenders = 0
    matches = len(myMatchHistory)
    for match in myMatchHistory:
        if match["Win_Status"] == "Win":
            wins += 1
        else:
            losses += 1
        kill = int(match["Kills"])
        death = int(match["Deaths"])
        kd = 0
        if(death == 0):
            kd = float(kill) / 1
        else:
            kd = float(kill) / death
        kills += kill
        if kill > mostKills:
            mostKills = kill
        deaths += death
        if death > mostDeaths:
            mostDeaths = death
        if kd > bestKD:
            bestKD = kd
        if kd < worstKD:
            worstKD = kd

    print("Data for last {0} games played by '{1}'.".format(matches, myMatchHistory[0]["playerName"]))
    print("Win average : {0}%".format(round(wins / matches * 100)))
    print("KD average : {:0.2f}".format(kills/deaths))
    print("Best KD : {:0.2f}".format(bestKD))
    print("Worst KD : {:0.2f}".format(worstKD))

def FriendStats(apiSession, username, allmembers, numbertoprint):
    getmatchhistory = apiSession.APICall("getmatchhistory", username)
    if getmatchhistory[0]["ret_msg"] != None:
        logging.error("Username '{}' has no match history. Check that it is spelled correctly.".format(username))
        sys.exit(-1)
    matchList = []
    playerStatList = PlayerStatList()
    for match in getmatchhistory:
        matchList.append([match["Match"],match["Win_Status"]])
    getfriends = apiSession.APICall("getfriends", username)
    friendsList = []
    for friend in getfriends:
        if friend["account_id"] != "0":
            friendsList.append(friend["name"])

    playerKill = 0
    playerDeath = 0
    friendKill = 0
    friendDeath = 0
    otherKill = 0
    otherDeath = 0
    gamesWithFriends = 0

    detailedMatches = []
    for matchID in matchList:
        detailedMatches.append(apiSession.APICall("getmatchdetails",matchID[0]))
    for detailedMatch in detailedMatches:
        matchOutcome = GetMatchOutcome(matchList, detailedMatch[0]["Match"])
        if matchOutcome == "Win":
            matchOutcome = "Winner"
        else:
            matchOutcome = "Loser"
        friendFound = False
        for player in detailedMatch:
            if not allmembers:
                if matchOutcome not in player["Win_Status"]:
                    continue
            if username in player["playerName"]:
                playerKill += player["Kills_Player"]
                playerDeath += player["Deaths"]
                playerStatList.addPlayerGame(username, player["Kills_Player"],player["Deaths"],player["Assists"])
            else:
                isFriend = False
                for friend in friendsList:
                    if friend in player["playerName"]:
                        isFriend = True
                if isFriend:
                    if not friendFound:
                        gamesWithFriends += 1
                        friendFound = True
                    friendKill += player["Kills_Player"]
                    friendDeath += player["Deaths"]
                    playerStatList.addPlayerGame(player["playerName"], player["Kills_Player"], player["Deaths"],player["Assists"])
                else:
                    otherKill += player["Kills_Player"]
                    otherDeath += player["Deaths"]
                    playerStatList.addPlayerGame(player["playerName"], player["Kills_Player"], player["Deaths"],player["Assists"])
    print("Data from last {0} games for player '{1}'".format(len(matchList),username))
    print("Game percentage played with at least one friend : {:0.0f}%".format(float(gamesWithFriends)/len(matchList) * 100))
    print("Player Kill Split : {0}-{1}".format(playerKill,playerDeath))
    print("Player KDR : {:0.2f}".format(playerKill/playerDeath))
    print("Friend Kill Split : {0}-{1}".format(friendKill,friendDeath))
    print("Friend KDR : {:0.2f}".format(friendKill/friendDeath))
    print("Other Kill Split : {0}-{1}".format(otherKill,otherDeath))
    print("Other KDR : {:0.2f}".format(otherKill/otherDeath))
    print()
    playerStatList.sort()
    for x in range(numbertoprint + 1):
        print(playerStatList.list[x])

def main():
    recordsToPrint = 100
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        print("Usage:")
        print("{} [Username]".format(sys.argv[0]))
        print("{} [Username] []".format(sys.argv[0]))
        sys.exit(-1)
    if len(sys.argv) == 3:
        recordsToPrint = int(sys.argv[2])
    if sys.stdout.encoding != 'cp65001':
        sys.stdout = codecs.getwriter('cp65001')(sys.stdout.buffer, 'strict')
    logging.basicConfig(level=logging.WARNING,
                        format='%(asctime)s:%(levelname)s:%(message)s')
    session = hirez.HiRezAPISession()
    FriendStats(session, sys.argv[1], False, recordsToPrint)

if __name__ == "__main__":
    main()