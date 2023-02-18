import xml.etree.ElementTree as ET
import json

xmlPath = "copper_acetate.xml"
with open(xmlPath, "r") as file:
    filedata = file.read()

filedata = filedata.replace(">&<", ">&amp;<")
filedata = filedata.replace("><<", ">&lt;<")
filedata = filedata.replace(">><", ">&gt;<")
with open(xmlPath, "w") as file:
    file.write(filedata)

tree = ET.parse(xmlPath)  # improvement: change to argument based input
root = tree.getroot()

output = {}
output["fullText"] = ""
output["title & info"] = ""

sectionTitleBuf = ""  # keeps track of new section title, empty while populating section
currSection = "title & info"

# hardcode
ignoredSections = [
    "The Journal of Organic Chemistry",
    "pubs.acs.org/joc",
    "*",
    "Received:",
    "Published:",
]

# hardcode
weirdChar = {
    "\u2212": "-", # long dash
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\u25a0": "", # black block
    "fraction(-)": "", # weird output of SymbolScraper
}
for word in root.iter("Word"):
    wordBuf = ""
    for char in word.iter("Char"):

        # ignore side vertical notes (hardcode)
        location = char.attrib["BBOX"].split(" ")[0]
        if location in ["9.0", "18.0"]:
            continue

        # writing section title (hardcode)
        if char.attrib["RGB"] == "[1.0]":
            sectionTitleBuf += str(char.text)
        # create new section
        elif sectionTitleBuf:
            if sectionTitleBuf.strip(" \u25a0") in ignoredSections:
                sectionTitleBuf = ""
            else:
                output[currSection] = output[currSection][
                    : -len(sectionTitleBuf) - 1
                ]  # strip the front and end
                sectionTitleBuf = sectionTitleBuf.strip(" \u25a0:").lower()
                output[sectionTitleBuf] = ""
                currSection = sectionTitleBuf
                sectionTitleBuf = ""

        # replace weirdly parsed unicode with actual text
        wordBuf += weirdChar[str(char.text)] if char.text in weirdChar else str(char.text)
    output["fullText"] += wordBuf
    output["fullText"] += " " if wordBuf and wordBuf[-1] != "-" else ""
    output[currSection] += wordBuf
    output[currSection] += " " if wordBuf and wordBuf[-1] != "-" else ""
    sectionTitleBuf += " " if sectionTitleBuf else ""

with open("sample.json", "w") as outfile:
    json.dump(output, outfile, indent=4)
