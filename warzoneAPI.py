#/bin/python3
'''
pip3 install bs4
pip3 install lxml
pip3 install requests
'''
import sys
import requests
import re
from bs4 import BeautifulSoup
import pickle
import json 
import sys

import os.path
from os import path

import urllib.parse
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


proxies = {
	'http' : 'http://172.17.192.1:8080','https' : 'http://172.17.192.1:8080'
}
proxies=None

# Define some variables 
url_initialize = 'https://s.activision.com/activision/login'
url_login = "https://s.activision.com/do_login?new_SiteId=activision"
url_identity = "https://www.callofduty.com/api/papi-client/crm/cod/v2/identities"

url_activision = "https://www.activision.com/"

username = ""
password = ""

profileName = urllib.parse.quote_plus(sys.argv[1])
platform = sys.argv[2]

cookies = ""

s = requests.session()

# Save Cookies to File 
def save_cookies(requests_cookiejar, filename):
    with open(filename, 'wb') as f:
        pickle.dump(requests_cookiejar, f)

def load_cookies(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

def new_request():
    r = s.get(url_initialize,proxies=proxies,verify=False)

    soup = BeautifulSoup(r.text, "lxml")
    csrf = soup("input", {"name": "_csrf"})[0]["value"]



    login = {
            "username": username,
            "remember_me": "true",
            "password": password,
            "_csrf": csrf
    }

    # Post request Execution
    r = s.post(url_login,data=login,proxies=proxies,verify=False)



    cookiesJar = s.cookies
    
    save_cookies(cookiesJar,"warzone.cookie")
    
    return cookiesJar
    
if path.exists("warzone.cookie") :
    cookiesJar = load_cookies("warzone.cookie")
else :
    cookiesJar = new_request()

dict_apiCookies = cookiesJar.get_dict()

cookies = {
            "ACT_SSO_COOKIE": dict_apiCookies["ACT_SSO_COOKIE"],
            "ACT_SSO_COOKIE_EXPIRY": dict_apiCookies["ACT_SSO_COOKIE_EXPIRY"],
            "atkn": dict_apiCookies["atkn"]
}


'''
curl --location --request GET 'https://my.callofduty.com/api/papi-client/crm/cod/v2/title/mw/platform/battle/gamer/engels/matches/wz/start/0/end/0/details' \
--header 'Cookie: ACT_SSO_COOKIE=Set by test scripts; ACT_SSO_COOKIE_EXPIRY=1591153892430; atkn=Set by test scripts;'


https://www.callofduty.com/api/papi-client/crm/cod/:version/title/:game/platform/battle/fullMatch/:mode/:matchId/it
'''

url_api_user_req = "https://www.callofduty.com/api/papi-client/stats/cod/v1/title/mw/platform/"+ platform +"/gamer/" + profileName + "/profile/type/wz"
r = s.get(url_api_user_req, cookies= cookies, proxies=proxies, verify=False)

json_object = json.loads(r.text)

if json_object["status"] == "error":
    print("Unable to get the profile: " + json_object["data"]["message"])
    sys.exit()

username = json_object["data"]["username"]
wins = json_object["data"]["lifetime"]["mode"]["br"]["properties"]["wins"]
kdRatio = json_object["data"]["lifetime"]["mode"]["br"]["properties"]["kdRatio"]
kills = json_object["data"]["lifetime"]["mode"]["br"]["properties"]["kills"]
timePlayed = json_object["data"]["lifetime"]["mode"]["br"]["properties"]["timePlayed"]

print("Username: " + username)
print("Wins: " + str(int(wins)))
print("KD: " + "{:.2f}".format(kdRatio))
print("Kills: " + str(int(kills)))
print("Time Played: " + "{:}".format(timePlayed/60) + " horas")

print()

'''
# List top 20 matches
https://my.callofduty.com/api/papi-client/crm/cod/v2/title/mw/platform/battle/gamer/EnGeLs%2311982/matches/wz/start/0/end/0/details

# Match Details:
https://www.callofduty.com/api/papi-client/crm/cod/v2/title/mw/platform/battle/fullMatch/wz/13870263487648849402/it
'''

#Search Profile 
url_search_profile = "https://my.callofduty.com/api/papi-client/crm/cod/v2/title/mw/platform/" + platform + "/gamer/" + profileName + "/matches/wz/start/0/end/0/details"

r = s.get(url_search_profile, cookies= cookies, proxies=proxies, verify=False)

profile_object = json.loads(r.text)

matchID = profile_object["data"]["matches"][0]["matchID"]
teamName = profile_object["data"]["matches"][0]["player"]["team"]

# Search Last Match 
url_search_match = "https://www.callofduty.com/api/papi-client/crm/cod/v2/title/mw/platform/battle/fullMatch/wz/"+matchID+"/it"
r = s.get(url_search_match, cookies= cookies, proxies=proxies, verify=False)

match_object = json.loads(r.text)
teamPlacement = ""
'''
# Get information from the match to identify player KD on this match 
for playerID in match_object["data"]["allPlayers"]:
    # Get Player ID 
    username = playerID["player"]["username"]
    uno = playerID["player"]["uno"]
    
    url_search_usersprofiles = "https://my.callofduty.com/api/papi-client/crm/cod/v2/platform/all/username/"+username+"/search"
    r = s.get(url_search_usersprofiles, cookies= cookies, proxies=proxies, verify=False)
    
    # Get Users Profiles to search for the correct one 
    usersprofiles_object = json.loads(r.text)
    
    for player in usersprofiles_object["data"]:
        url_player_matches = "https://my.callofduty.com/api/papi-client/crm/cod/v2/title/mw/platform/"+ player["platform"] +"/gamer/" + urllib.parse.quote_plus(player["username"]) + "/matches/wz/start/0/end/0/details"
        
        r = s.get(url_player_matches, cookies= cookies, proxies=proxies, verify=False)
        user_matches_object = json.loads(r.text)
        
        if user_matches_object["status"] == "error":
            break
        
        print("User Found: " + player["username"])
        
        for match in user_matches_object["data"]["matches"]:
            if match["matchID"] == matchID:
                url_api_user_profile = "https://www.callofduty.com/api/papi-client/stats/cod/v1/title/mw/platform/"+ player["platform"] +"/gamer/" + urllib.parse.quote_plus(player["username"]) + "/profile/type/wz"
                
                r = s.get(url_api_user_profile, cookies= cookies, proxies=proxies, verify=False)

                json_object = json.loads(r.text)
                username = json_object["data"]["username"]
                kdRatio = json_object["data"]["lifetime"]["mode"]["br"]["properties"]["kdRatio"]
                
                print("User Found: " + player["username"] + " KD: " + "{:.2f}".format(kdRatio))
                break
        break        
        #print("[+] Username " + username + " KD: " + 
'''

for match in profile_object["data"]["matches"]:
    matchID = match["matchID"]
    teamName = match["player"]["team"]
    url_search_match = "https://www.callofduty.com/api/papi-client/crm/cod/v2/title/mw/platform/battle/fullMatch/wz/"+matchID+"/it"
    r = s.get(url_search_match, cookies= cookies, proxies=proxies, verify=False)
    match_object = json.loads(r.text)

    print("### Match " + matchID + "###")

    for playerID in match_object["data"]["allPlayers"]:
        if playerID["player"]["team"] == teamName:
            print("[+] Useranme: " + playerID["player"]["username"])
            print("kills " + str(int(playerID["playerStats"]["kills"])))
            print("deaths " + str(int(playerID["playerStats"]["deaths"])))
            print("kdRatio " + "{:.2f}".format(playerID["playerStats"]["kdRatio"]))
            print("gulagKills " + str(int(playerID["playerStats"]["gulagKills"])))
            print("assists " + str(int(playerID["playerStats"]["assists"])))
            print("damageDone " + str(int(playerID["playerStats"]["damageDone"])))
            print("damageTaken " + str(int(playerID["playerStats"]["damageTaken"])))
            teamPlacement = playerID["playerStats"]["teamPlacement"]
            print()
    print("[+] Team Placement: " + str(int(teamPlacement)))
    print()
