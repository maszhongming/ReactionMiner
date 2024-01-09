import getopt
import json
import os
import sys
import xml.etree.ElementTree as ET

from . import config
from .helpers import fileIOHelper, logHelper, pdfToXmlHelper, xmlToJsonHelper
from .postprocess import cleanJson

projectPath = os.path.dirname(os.path.abspath(__file__))


def parseFile(pdfPath: str, logging=False):
    # given a path to a pdf file, parse the pdf file and output a json file
    # both symbol scraper and xml parser are run

    # check if pdf file exists
    if not os.path.exists(pdfPath):
        print("Error: File does not exist:", pdfPath)
        return -1
    pdfPath = os.path.abspath(pdfPath)
    filename = os.path.basename(pdfPath)[: -len(".pdf")]
    xmlPath = projectPath + "/xmlFiles/" + filename + ".xml"
    rawJsonPath = projectPath + "/parsed_raw/" + filename + ".json"
    cleanJsonPath = projectPath + "/results/" + filename + ".json"
    pdfDirPath = os.path.dirname(pdfPath)
    xmlDirPath = os.path.dirname(xmlPath)

    # create xml dir if not exist
    if not os.path.exists(xmlDirPath):
        os.mkdir(xmlDirPath)

    # step 1: parse pdf into xml using Symbol Scraper
    print("Step 1: Parse PDF into XML using Symbol Scraper")
    # don't run SymbolScraper if xml already parsed
    if os.path.exists(xmlPath):
        print("XML file already exists:", xmlPath)
    else:
        print("Parsing", pdfPath)
        suppressSymbolScraperOutput = True
        outputOption = " > /dev/null" if suppressSymbolScraperOutput else ""
        os.system(projectPath + "/SymbolScraper/bin/sscraper " + pdfPath + " " + xmlDirPath + outputOption)
        if not os.path.exists(xmlPath):
            print("Error: SymbolScraper failed to parse", pdfPath)
            logHelper.errorLog(pdfPath)
            return -1
        print("XML file written to:", xmlPath)

    # step 2: parse xml into raw json
    print("Step 2: Parse XML into raw JSON")
    # don't parse xml if json already exists
    if os.path.exists(rawJsonPath):
        print("JSON file already exists:", rawJsonPath)
    else:
        parseExitCode = parse(xmlPath)
        if parseExitCode == -1:
            print("Error: Parse XML failed, skipping", pdfPath)
            return -1

    # step 3: clean json
    print("Step 3: Clean JSON file")
    # don't clean json if clean json already exists
    if os.path.exists(cleanJsonPath):
        print("Clean JSON file already exists:", cleanJsonPath)
    else:
        cleanJson(rawJsonPath)

    # clean up useless .md files created by SymbolScraper
    print('pdfDirPath', pdfDirPath)
    for file in os.listdir(pdfDirPath):
        if file.endswith(".md") and file != "README.md":
            os.remove(pdfDirPath + "/" + file)

    print("Finished parsing", pdfPath, "\n")
    # write to the end of log.txt with timestamp
    if logging:
        logHelper.successLog(pdfPath)

    # return the clean json object
    with open(cleanJsonPath, "r") as f:
        return json.load(f)


def parseFolder(folderPath: str, logging=False):
    # given a path to a folder, recursively parse all pdf files in it

    for item in sorted(os.listdir(folderPath)):
        itemPath = os.path.join(folderPath, item)
        if itemPath.endswith(".pdf"):
            validPath = fileIOHelper.validateFilename(itemPath)
            parseFile(validPath, logging=logging)
        elif os.path.isdir(itemPath):
            validPath = fileIOHelper.validateFilename(itemPath)
            parseFolder(validPath, logging=logging)


def parse(inputXml: str, logging=False):
    # given a path to a xml file, parse the xml file and output a json file

    pdfToXmlHelper.preParseXML(inputXml)
    try:
        tree = ET.parse(inputXml)  # improvement: change to argument based input
    except ET.ParseError:
        print("Error: Parse XML failed, skipping", inputXml)
        if logging:
            logHelper.errorLog(inputXml)
        return -1
    root = tree.getroot()

    output = {}
    output["fullText"] = ""
    output["contents"] = []

    paragraphStart = xmlToJsonHelper.findOffset(root)

    for pageXml in root.iter("Page"):
        prevLineBBOX = None
        for lineXml in pageXml.iter("Line"):
            # building line content
            lineContent = ""
            lineXMLBBOX = lineXml.attrib["BBOX"]
            for wordXml in lineXml.iter("Word"):
                word = xmlToJsonHelper.buildWord(wordXml)
                lineContent = xmlToJsonHelper.updateText(lineContent, word)
            lineContent = lineContent.strip()

            # if the line is a graph, skip the rest of the page
            # fullText will not have the rest of page either
            if xmlToJsonHelper.checkEndOfPage(lineContent) and xmlToJsonHelper.checkNewParagraph(lineXMLBBOX, prevLineBBOX, paragraphStart):
                break
            # update outputs
            output["fullText"] = xmlToJsonHelper.updateText(output["fullText"], lineContent)
            if xmlToJsonHelper.checkNewParagraph(lineXMLBBOX, prevLineBBOX, paragraphStart):
                output["contents"].append(lineContent)
            else:
                output["contents"][-1] = xmlToJsonHelper.updateText(output["contents"][-1], lineContent)
            # update prevLineBBOX
            if xmlToJsonHelper.checkSameLine(lineXMLBBOX, prevLineBBOX):
                prevLineBBOX = xmlToJsonHelper.combineLines(lineXMLBBOX, prevLineBBOX)
            else:
                prevLineBBOX = lineXMLBBOX
    # output raw json file
    filename = os.path.basename(inputXml)[: -len(".xml")]
    fileIOHelper.outputDirtyJsonFile(filename, output)


# main function
if __name__ == "__main__":
    argv = sys.argv[1:]
    inputfile = ""
    opts, args = getopt.getopt(argv, "hcli:")
    for opt, arg in opts:
        if opt == "-h":
            print("[Usage]: python3 generalParser.py -i <inputPDF>")
            print("Result will be saved as a .json file in the results/ folder")
            sys.exit()
        elif opt == "-i":
            inputfile = arg
            parseFile(inputfile)
        elif opt == "-c":
            fileIOHelper.cleanFolders()
        elif opt == "-l":
            target_dir = os.path.join(projectPath, config.defaultDir)
            logHelper.logHeader()
            parseFolder(target_dir, logging=True)
    if not opts:
        target_dir = os.path.join(projectPath, config.defaultDir)
        parseFolder(target_dir)
