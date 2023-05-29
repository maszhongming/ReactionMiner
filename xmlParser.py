import xml.etree.ElementTree as ET
import collections
import json
import os
import sys, getopt
import re
import shutil

defaultDir = "bio_paper"

weirdChar = {
    "\u2212": "-",  # long dash
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "fraction(-)": "",  # weird output of SymbolScraper
    "\u25a0": "",
}

ignoredSuffix = {
    "*S Supporting Information",
    "Received:",
    "Published:",
    "pubs.acs.org",
    "©",
    "J. Org. Chem.",
    "Article",
    "The Journal of Organic Chemistry Article",
    "DOI: ",
    "Cite This:",
    "ACCESS",
    "Metrics & More Article Recommendations",
    "*sı",
    "Supporting Information",
    "https://doi.org/",
}

singleParagraphSection = [
    "abstract",
    "title & info",
]


def preParseXML(path):
    with open(path, "r") as file:
        filedata = file.read()
    filedata = filedata.replace(">&<", ">&amp;<")
    filedata = filedata.replace("><<", ">&lt;<")
    filedata = filedata.replace(">><", ">&gt;<")
    filedata = filedata.replace("", "")
    filedata = filedata.replace(chr(0), "")
    for invalidAscii in range(1, 31):
        if invalidAscii == 9 or invalidAscii == 10 or invalidAscii == 13:
            continue   # tab, newline, carriage return 
        char = chr(invalidAscii)
        filedata = filedata.replace(char, "")
    with open(path, "w") as file:
        file.write(filedata)


def updateText(inputObject, word):
    if isinstance(inputObject, str):
        inputObject += word
        inputObject += " " if word and word[-1] != "-" else ""
    else:
        inputObject[-1] += word
        inputObject[-1] += " " if word and word[-1] != "-" else ""
    return inputObject


def checkStartSection(lineXml):
    for char in lineXml.iter("Char"):
        # detect blue square for new section
        if char.text == "\u25a0":
            return True
    return False


def buildWord(wordXml):
    wordBuf = ""
    for char in wordXml.iter("Char"):
        wordBuf += (
            weirdChar[str(char.text)] if char.text in weirdChar else str(char.text)
        )
    return wordBuf


def checkSideLine(lineXml):
    location = lineXml.attrib["BBOX"].split(" ")[0]
    return location in ["9.0", "18.0"]


def checkIgnoredPrefix(line):
    for prefix in ignoredSuffix:
        if line.startswith(prefix):
            return True
    return False


def outputJsonFile(xmlPath, output):
    outputFileName = xmlPath.split("/")[-1][:-4] + ".json"
    path = os.getcwd()
    result_directory = path + "/result/"
    if not os.path.exists(result_directory):
        os.mkdir(result_directory)
    outputFileName = result_directory + outputFileName
    with open(outputFileName, "w") as outfile:
        json.dump(output, outfile, indent=4)
    print("Parsed pdf successfully written to", outputFileName)


def findOffset(root):
    lineStartPos = collections.defaultdict(int)
    for lineXml in root.iter("Line"):
        location = round(float(lineXml.attrib["BBOX"].split(" ")[0]))
        lineStartPos[location] += 1
    twoMean = sorted(lineStartPos.items(), key=lambda x: x[1], reverse=True)[:2]
    res = [twoMean[0][0], twoMean[1][0]]
    return res


def checkStartParagrph(lineXml, paragraphStart):
    location = round(float(lineXml.attrib["BBOX"].split(" ")[0]))
    return location - 9 in paragraphStart or location - 10 in paragraphStart


def checkEndOfPage(text):
    if re.match("^(scheme|table|figure) [1-9]. ", text):
        return True
    else:
        return False

def validateFilename(inputfile: str):
    newFilename = inputfile.replace(" ", "_").replace("(", "_").replace(")", "_")
    os.rename(inputfile, newFilename)
    return newFilename


def parseFile(pdfPath: str):
    # create temp dir if not exist
    tempDirPath = "./xmlFiles/"
    if not os.path.exists(tempDirPath):
        os.mkdir(tempDirPath)
    # don't run SymbolScraper if xml already parsed
    xmlPath = tempDirPath + pdfPath.split("/")[-1][:-4] + ".xml"
    if os.path.exists(xmlPath):
        print("XML file already exists")
        print("xmlpath", xmlPath)
    else:
        print("Parsing", pdfPath)
        os.system(
            "SymbolScraper/bin/sscraper " + pdfPath + " " + tempDirPath + " > /dev/null"
        )
    # don't parse xml if json already exists
    targetJsonPath = os.getcwd() + "/result/" + pdfPath.split("/")[-1][:-4] + ".json"
    if os.path.exists(targetJsonPath):
        print("JSON file already exists")
        return
    else:    
        parse(xmlPath)
    # clean up useless .md files created by SymbolScraper
    pdfDirPath = os.path.dirname(pdfPath)
    for mdFile in os.listdir(pdfDirPath):
        if mdFile.endswith(".md") and mdFile != "README.md":
            os.remove(pdfDirPath + "/" + mdFile)

# parse all files in a folder
def parseFolder(folderPath: str):
    for item in sorted(os.listdir(folderPath)):
        itemPath = os.path.join(folderPath, item)
        if itemPath.endswith(".pdf"):
            validPath = validateFilename(itemPath)
            parseFile(validPath)
        elif os.path.isdir(itemPath):
            validPath = validateFilename(itemPath)
            parseFolder(validPath)
        print()

def parse(inputXml: str):
    preParseXML(inputXml)
    tree = ET.parse(inputXml)  # improvement: change to argument based input
    root = tree.getroot()

    output = {}
    output["fullText"] = ""
    output["title & info"] = ""
    output["abstract"] = ""
    currSection = "title & info"
    newSectionFlag = False

    paragraphStart = findOffset(root)

    # parsing logic: check the black square, flag=1 when square is encountered
    # use the next line as new section title
    for pageXml in root.iter("Page"):
        for lineXml in pageXml.iter("Line"):
            if checkSideLine(lineXml):
                continue
            if checkStartSection(lineXml):
                newSectionFlag = True
                continue
            if (
                checkStartParagrph(lineXml, paragraphStart)
                and currSection not in singleParagraphSection
                and output[currSection][-1]
            ):
                output[currSection][-1] = output[currSection][-1].strip()
                output[currSection].append("")
            line = ""
            for wordXml in lineXml.iter("Word"):
                word = buildWord(wordXml)
                line = updateText(line, word)
            line = line.strip()
            if checkIgnoredPrefix(line):
                continue

            # update outputs
            output["fullText"] = updateText(output["fullText"], line)
            # blue square is always by itself on a line, so sectionTitleBuf is fully populated here
            # either write to a new section title or an existing section's content
            if newSectionFlag:
                if currSection in singleParagraphSection:
                    output[currSection] = output[currSection].strip()
                else:
                    output[currSection][-1] = output[currSection][-1].strip()
                currSection = line.lower()
                output[currSection] = []
                output[currSection].append("")
                newSectionFlag = False
            elif line.lower().startswith("abstract:"):
                # print(output)
                output["title & info"] = output["title & info"].strip()
                currSection = "abstract"
                output["abstract"] += line[len("abstract:") :].strip()
            elif checkEndOfPage(line.lower()):
                break
            else:
                output[currSection] = updateText(output[currSection], line)

    outputJsonFile(inputXml, output)

# clear everything in the xml and result folder
def cleanFolders():
    path = os.getcwd()
    xml_directory = path + "/xmlFiles/"
    result_directory = path + "/result/"
    if os.path.exists(xml_directory):
        shutil.rmtree(xml_directory)
    if os.path.exists(result_directory):
        shutil.rmtree(result_directory)

if __name__ == "__main__":
    argv = sys.argv[1:]
    inputfile = ""
    opts, args = getopt.getopt(argv, "hi:")
    for opt, arg in opts:
        if opt == "-h":
            print("[Usage]: python3 xmlParser.py -i <inputPDF>")
            print("Result will be saved as a .json in ./result/")
            sys.exit()
        elif opt == "-i":
            inputfile = arg
            parseFile(inputfile)
    if not opts:
        # cleanFolders()
        cwd = os.getcwd()
        target_dir = os.path.join(cwd, defaultDir)
        parseFolder(target_dir)
