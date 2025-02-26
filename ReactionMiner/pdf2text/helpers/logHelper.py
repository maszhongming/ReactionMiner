import datetime
import os

projectPath = os.path.dirname(os.path.abspath(__file__)) + "/../"
logPath = projectPath + "/log.txt"
errorLogPath = projectPath + "/errorLog.txt"


def logHeader():
    with open(logPath, "a") as logFile:
        currentTime = datetime.datetime.now()
        logFile.write(currentTime.strftime("%Y-%m-%d %H:%M:%S") + "start running the parser\n")
    with open(errorLogPath, "a") as errorLogFile:
        currentTime = datetime.datetime.now()
        errorLogFile.write(currentTime.strftime("%Y-%m-%d %H:%M:%S") + "start running the parser\n")


def successLog(pdfPath):
    with open(logPath, "a") as logFile:
        currentTime = datetime.datetime.now()
        basename = os.path.basename(pdfPath)
        logFile.write(currentTime.strftime("%Y-%m-%d %H:%M:%S") + " " + basename + "\n")


def errorLog(pdfPath):
    with open(errorLogPath, "a") as logFile:
        currentTime = datetime.datetime.now()
        basename = os.path.basename(pdfPath)
        logFile.write(currentTime.strftime("%Y-%m-%d %H:%M:%S") + " " + basename + "\n")
