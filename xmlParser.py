import xml.etree.ElementTree as ET
import collections
import json
import os
import sys, getopt

weirdChar = {
    "\u2212": "-",  # long dash
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
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


def checkEndOfPage(lineXml, prevLocation):
    location = lineXml.attrib["BBOX"].split(" ").float()
    if location[0] < prevLocation[0] and location[1] < prevLocation:
        return True


def main(inputfile: str):
    temp_dir = "./xmlFiles"
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)
    print("sscraper " + inputfile + " " + temp_dir)
    os.system(
        "SymbolScraper/bin/sscraper " + inputfile + " " + temp_dir + " > /dev/null"
    )
    # for inputXml in xmlPaths:
    for filename in os.listdir(temp_dir):
        if filename.endswith(".xml"):
            inputXml = os.path.join(temp_dir, filename)
            parse(inputXml)
            # os.remove(inputXml)
    for mdFile in os.listdir(os.getcwd()):
        if mdFile.endswith(".md") and mdFile != "README.md":
            os.remove(mdFile)
    # os.removedirs(temp_dir)


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
    for lineXml in root.iter("Line"):

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
            output["title & info"] = output[currSection].strip()
            currSection = "abstract"
            output["abstract"] += line[len("abstract:") :].strip()
        else:
            output[currSection] = updateText(output[currSection], line)

    outputJsonFile(inputXml, output)


if __name__ == "__main__":
    argv = sys.argv[1:]
    inputfile = ""
    opts, args = getopt.getopt(argv, "hi:")
    for opt, arg in opts:
        if opt == "-h":
            print("[Usage]: xmlParser.py -i <inputPDF>")
            print("Result will be saved as a .json in ./result/")
            sys.exit()
        # elif opt == "-i":
        else:
            inputfile = arg
            main(inputfile)
