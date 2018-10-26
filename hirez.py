from time import gmtime, strftime
import urllib.request
import json
import logging as log
import os
import re
import sys
import hashlib
import http.client as httplib

def TextFileToStringList(path):
    if os.path.exists(path):
        with open(path, 'r') as myfile:
            data = myfile.read().split('\n')
        return data

def TextFileToString(path):
    if os.path.exists(path):
        with open(path, 'r') as myfile:
            data = myfile.read()
        return data

def StringToTextFile(path,string):
    text_file = open(path, "w")
    text_file.write(string)
    text_file.close()

def Time():
    return strftime("%Y%m%d%H%M%S", gmtime())

def MD5Hash(string):
    return hashlib.md5(string.encode('utf-8')).hexdigest()

def HaveInternet():
    conn = httplib.HTTPConnection("www.google.com", timeout=1)
    try:
        conn.request("HEAD", "/")
        conn.close()
        return True
    except:
        conn.close()
        return False

class HiRezAPIException(Exception):
    def __init__(self, message):
        super().__init__(message)

class HiRezAPISession:
    def __init__(self):
        if not HaveInternet():
            raise HiRezAPIException("No internet connection available.")
        self.cacheAllResponses = False
        self.reqBase = "http://api.smitegame.com/smiteapi.svc/"
        self.utilFilePath = os.path.join("C:\\", "ProgramData", "HiRezAPISession")
        os.makedirs(self.utilFilePath, exist_ok=True)
        self.credentialsFile = os.path.join(self.utilFilePath, "credentials.txt")
        if not os.path.exists(self.credentialsFile):
            raise HiRezAPIException("Credentials file is missing. Add credentials.txt to {0}".format(self.utilFilePath))
        getCred = TextFileToStringList(self.credentialsFile)
        if len(getCred) != 2:
            raise HiRezAPIException("Credentials file does not have the correct number of lines.")
        if not re.match("[0-9]+",getCred[0]):
            raise HiRezAPIException("devId field of credentials file is incorrect.")
        if not re.match("[0-9A-F]+",getCred[1]):
            raise HiRezAPIException("AuthKey field of credentials file is incorrect.")
        self.devID = getCred[0]
        self.authKey = getCred[1]
        log.debug("devID:{0}".format(self.devID))
        log.debug("authKey:{0}".format(self.authKey))
        self.sessionFile = os.path.join(self.utilFilePath, "session.txt")
        self.previousSession = os.path.exists(self.sessionFile)
        self.sessionID = ""
        if not self.previousSession:
            log.debug("No cached session found. Starting new session.")
            self.__StartSession()
        else:
            log.debug("Cached session found.")
            sessionFile = TextFileToString(self.sessionFile)
            parseSessionFile = json.loads(sessionFile)
            log.debug("sessionFile session_id:{0}".format(parseSessionFile["session_id"]))
            self.sessionID = parseSessionFile["session_id"]
            if "This was a successful test" not in self.APICall("testsession"):
                log.debug("Cached session was invalid, creating a new session.")
                self.__StartSession()
            else:
                log.debug("Cached session was still valid, reusing session.")

    def __StartSession(self):
       startSessionReq = self.reqBase + "createsessionJson/" +  self.devID + "/" + self.__Signature("createsession") + "/" + Time()
       startSessionResp = ""
       try:
           startSessionResp = urllib.request.urlopen(startSessionReq).read()
       except Exception as e:
           print(e)
           sys.exit(1)
       parseResp = json.loads(startSessionResp.decode())
       log.debug(json.dumps(parseResp, indent=4))
       if parseResp["ret_msg"] != "Approved":
           raise HiRezAPIException("HiRez API request was refused : {0}".format(parseResp["ret_msg"]))
       StringToTextFile(self.sessionFile, json.dumps(parseResp, indent=4))
       self.sessionID = parseResp["session_id"]

    def __Signature(self, method):
       return MD5Hash(self.devID + method + self.authKey + Time())

    def APICall(self, *args):
        tempName = ""
        for arg in args:
            tempName += str(arg)
        tempName += ".json"
        if os.path.exists(os.path.join(self.utilFilePath,tempName)) and self.cacheAllResponses:
            log.debug("Found cached request, returning...")
            return json.loads(TextFileToString(os.path.join(self.utilFilePath,tempName)))
        if os.path.exists(os.path.join(self.utilFilePath, tempName)) and not self.cacheAllResponses:
            log.debug("Found cached request but cacheAllResponses is false, ignoring...")
        toReturn = None
        callBase = "http://api.smitegame.com/smiteapi.svc/" + args[0] + "Json/" + self.devID + "/" + \
        self.__Signature(args[0]) + "/" + self.sessionID + "/" + Time()
        iter = 1
        while iter < len(args):
            callBase += "/{0}".format(args[iter])
            iter += 1

        scheme, netloc, path, query, fragment = urllib.parse.urlsplit(callBase)
        path =  urllib.parse.quote(path)
        callBase =  urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))

        toReturn = urllib.request.urlopen(callBase).read()
        temp = json.loads(toReturn.decode())
        if self.cacheAllResponses and args[0] != "testsession":
            log.debug("Caching request '{}'...".format(tempName))
            StringToTextFile(os.path.join(self.utilFilePath,tempName),json.dumps(temp, indent=4))
        return temp

    def Status(self):
        return self.APICall("getdataused")