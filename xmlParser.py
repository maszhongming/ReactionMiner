import xml.etree.ElementTree as ET
import collections
import json

xmlPath = "copper_acetate.xml"
# xmlPath = "test2.xml"


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
    "J. Org. Chem. 2015, 80, 4116-4122",
    "Article",
    "The Journal of Organic Chemistry Article",
    "DOI: "
}


def preParseXML(path):
    with open(path, "r") as file:
        filedata = file.read()
    filedata = filedata.replace(">&<", ">&amp;<")
    filedata = filedata.replace("><<", ">&lt;<")
    filedata = filedata.replace(">><", ">&gt;<")
    with open(path, "w") as file:
        file.write(filedata)


def updateText(text, word):
    text += word
    text += " " if word and word[-1] != "-" else ""
    return text


def checkStartSection(wordXml):
    for char in wordXml.iter("Char"):
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


def main():
    preParseXML(xmlPath)
    tree = ET.parse(xmlPath)  # improvement: change to argument based input
    root = tree.getroot()

    output = collections.defaultdict(str)
    # keeps track of new section title, empty while populating section
    sectionTitleBuf = ""
    currSection = "title & info"

    # ignoredSections = [
    #     "The Journal of Organic Chemistry",
    #     "pubs.acs.org/joc",
    #     "*",
    #     "Received:",
    #     "Published:",
    # ]

    newSectionFlag = False

    # parsing logic: check the black square, flag=1 when square is encountered
    # use the next line as new section title
    for lineXml in root.iter("Line"):
        if checkSideLine(lineXml):
            continue
        line = ""
        for wordXml in lineXml.iter("Word"):
            if checkStartSection(wordXml):
                sectionTitleBuf = ""
                newSectionFlag = True
            word = buildWord(wordXml)
            # update outputs
            # non-section-title word goes into currSection, section-title word goes into sectionTitleBuf
            line = updateText(line, word)
        line = line.strip()
        if checkIgnoredPrefix(line):
            continue
        print(line)
        output["fullText"] = updateText(output["fullText"], line)
        if newSectionFlag:
            sectionTitleBuf = updateText(sectionTitleBuf, line)
        else:
            output[currSection] = updateText(output[currSection], line)

        # blue square is always by itself on a line, so sectionTitleBuf is fully populated here
        if newSectionFlag and sectionTitleBuf:
            output[currSection] = output[currSection].strip()
            currSection = sectionTitleBuf.strip().lower()
            sectionTitleBuf = ""
            newSectionFlag = False

    with open("sample.json", "w") as outfile:
        json.dump(output, outfile, indent=4)


main()
