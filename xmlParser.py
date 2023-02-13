import xml.etree.ElementTree as ET

tree = ET.parse("./acs.joc.5b00443.xml")
root = tree.getroot()

allText = ''
for word in root.iter('Word'):
    wordBuf = ''
    for char in word.iter('Char'):
        wordBuf += str(char.text)
    allText += wordBuf + ' '

print(allText)
