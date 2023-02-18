import xml.etree.ElementTree as ET
import collections
import json

# xmlPath = "copper_acetate.xml"
xmlPath = "test2.xml"


def preParseXML(path):
    with open(path, "r") as file:
        filedata = file.read()
    filedata = filedata.replace(">&<", ">&amp;<")
    filedata = filedata.replace("><<", ">&lt;<")
    filedata = filedata.replace(">><", ">&gt;<")
    with open(path, "w") as file:
        file.write(filedata)


def main():
    preParseXML(xmlPath)
    tree = ET.parse(xmlPath)  # improvement: change to argument based input
    root = tree.getroot()

    output = collections.defaultdict(str)
    # keeps track of new section title, empty while populating section
    sectionTitleBuf = ""
    currSection = "title & info"

    ignoredSections = [
        "The Journal of Organic Chemistry",
        "pubs.acs.org/joc",
        "*",
        "Received:",
        "Published:",
    ]

    weirdChar = {
        "\u2212": "-",  # long dash
        "\ufb00": "ff",
        "\ufb01": "fi",
        "\ufb02": "fl",
        "fraction(-)": "",  # weird output of SymbolScraper
        "\u25a0": "",
    }

    newSectionFlag = False
    # parsing logic: check the black square, flag=1 when square is encountered
    # use the next line as newSectionTitle
    for line in root.iter("Line"):
        for word in line.iter("Word"):
            wordBuf = ""
            for char in word.iter("Char"):
                # detect blue square for new section
                if char.text == "\u25a0":
                    print("here")
                    sectionTitleBuf = ""
                    newSectionFlag = True
                    continue
                # build word
                wordBuf += (
                    weirdChar[str(char.text)]
                    if char.text in weirdChar
                    else str(char.text)
                )

            # update fullText and currSection with spaces
            # every word goes into fullText
            output["fullText"] += wordBuf
            output["fullText"] += " " if wordBuf and wordBuf[-1] != "-" else ""
            # non-section-title word goes into currSection, section-title word goes into sectionTitleBuf
            if newSectionFlag:
                sectionTitleBuf += wordBuf
                sectionTitleBuf += " " if wordBuf else ""
            else:
                output[currSection] += wordBuf
                output[currSection] += " " if wordBuf and wordBuf[-1] != "-" else ""

        # blue square is always by itself on a line, so sectionTitleBuf is fully populated here
        if newSectionFlag and sectionTitleBuf:
            newSectionFlag = False
            currSection = sectionTitleBuf.strip().lower()
            sectionTitleBuf = ""

    with open("sample.json", "w") as outfile:
        json.dump(output, outfile, indent=4)

main()
