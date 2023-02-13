import xml.etree.ElementTree as ET
import json

tree = ET.parse("./acs.joc.5b00443.xml")
root = tree.getroot()

output = {}
output["fullText"] = ""
output["title & info"] = ""

sectionTitleBuf = ""  # keeps track of new section title, empty while populating section
currSection = "title & info"

ignoredSections = [
    "The Journal of Organic Chemistry",
    "pubs.acs.org/joc",
    "*",
    "Received:",
    "Published:",
]

weirdChar = {
    "\u2212": "-",
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "fraction(-)": "",
    "\u25a0": "",
}
for word in root.iter("Word"):
    wordBuf = ""
    for char in word.iter("Char"):

        # ignore side vertical notes
        location = char.attrib["BBOX"].split(" ")[0]
        if location in ["9.0", "18.0"]:
            continue
        # writing section title
        if char.attrib["RGB"] == "[1.0]":
            if char.text != "\u25a0":
                sectionTitleBuf += str(char.text)
        # create new section
        elif sectionTitleBuf:
            if sectionTitleBuf.strip() in ignoredSections:
                sectionTitleBuf = ""
            else:
                output[currSection] = output[currSection][
                    : -len(sectionTitleBuf) - 1
                ]  # strip the end
                sectionTitleBuf = sectionTitleBuf.strip().strip(":").lower()
                output[sectionTitleBuf] = ""
                currSection = sectionTitleBuf
                sectionTitleBuf = ""
        if char.text in weirdChar:
            wordBuf += weirdChar[str(char.text)]
            continue
        wordBuf += str(char.text)
    output["fullText"] += wordBuf
    output["fullText"] += " " if wordBuf and wordBuf[-1] != "-" else ""
    output[currSection] += wordBuf
    output[currSection] += " " if wordBuf and wordBuf[-1] != "-" else ""
    if sectionTitleBuf:
        sectionTitleBuf += " "

# print(output["allText"])
with open("sample.json", "w") as outfile:
    json.dump(output, outfile, indent=4)
