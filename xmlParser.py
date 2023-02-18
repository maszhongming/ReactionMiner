import xml.etree.ElementTree as ET
import collections
import json

xmlPaths = ["copper_acetate.xml", "test2.xml"]


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
    outputFileName = xmlPath.split("/")[-1].split(".")[0] + ".json"
    with open(outputFileName, "w") as outfile:
        json.dump(output, outfile, indent=4)
    print("Parsed pdf successfully written to", outputFileName)


def main():
    for inputXml in xmlPaths:
        # print(inputXml)
        preParseXML(inputXml)
        tree = ET.parse(inputXml)  # improvement: change to argument based input
        root = tree.getroot()

        output = collections.defaultdict(str)
        currSection = "title & info"
        newSectionFlag = False

        # parsing logic: check the black square, flag=1 when square is encountered
        # use the next line as new section title
        for lineXml in root.iter("Line"):
            if checkSideLine(lineXml):
                continue
            if checkStartSection(lineXml):
                newSectionFlag = True
                continue
            line = ""
            for wordXml in lineXml.iter("Word"):
                word = buildWord(wordXml)
                line = updateText(line, word)
            line = line.strip()
            if checkIgnoredPrefix(line):
                continue
            # print(line)

            # update outputs
            output["fullText"] = updateText(output["fullText"], line)
            # blue square is always by itself on a line, so sectionTitleBuf is fully populated here
            # either write to a new section title or an existing section's content
            if newSectionFlag:
                output[currSection] = output[currSection].strip()
                currSection = line.lower()
                newSectionFlag = False
            elif line.lower().startswith("abstract:"):
                output[currSection] = output[currSection].strip()
                currSection = "abstract"
                output["abstract"] += line[len("abstract:") :].strip()
            else:
                output[currSection] = updateText(output[currSection], line)

        outputJsonFile(inputXml, output)


main()
