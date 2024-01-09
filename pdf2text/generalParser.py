import xml.etree.ElementTree as ET
import os
import sys
import getopt
import helpers.pdfToXmlHelper as pdfToXmlHelper
import helpers.xmlToJsonHelper as xmlToJsonHelper
import helpers.fileIOHelper as fileIOHelper
import helpers.logHelper as logHelper
import config
from postprocess import cleanJson

projectPath = os.path.dirname(os.path.abspath(__file__))


def parseFile(pdfPath: str):
    # given a path to a pdf file, parse the pdf file and output a json file
    # both symbol scraper and xml parser are run

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
        suppressSymbolScraperOutput = False
        outputOption = " > /dev/null" if suppressSymbolScraperOutput else ""
        os.system(projectPath + "/SymbolScraper/bin/sscraper " + pdfPath + " " + xmlDirPath + outputOption)
        if not os.path.exists(xmlPath):
            print("Error: SymbolScraper failed to parse", pdfPath)
            logHelper.errorLog(pdfPath)
            return
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
            return

    # step 3: clean json
    print("Step 3: Clean JSON file")
    # don't clean json if clean json already exists
    if os.path.exists(cleanJsonPath):
        print("Clean JSON file already exists:", cleanJsonPath)
        return
    else:
        cleanJson(rawJsonPath)

    # clean up useless .md files created by SymbolScraper
    for file in os.listdir(pdfDirPath):
        if file.endswith(".md") and file != "README.md":
            os.remove(pdfDirPath + "/" + file)

    print("Finished parsing", pdfPath, "\n")
    # write to the end of log.txt with timestamp
    logHelper.successLog(pdfPath)


def parseFolder(folderPath: str):
    # given a path to a folder, recursively parse all pdf files in it

    for item in sorted(os.listdir(folderPath)):
        itemPath = os.path.join(folderPath, item)
        if itemPath.endswith(".pdf"):
            validPath = fileIOHelper.validateFilename(itemPath)
            parseFile(validPath)
        elif os.path.isdir(itemPath):
            validPath = fileIOHelper.validateFilename(itemPath)
            parseFolder(validPath)


def parse(inputXml: str):
    # given a path to a xml file, parse the xml file and output a json file

    pdfToXmlHelper.preParseXML(inputXml)
    try:
        tree = ET.parse(inputXml)  # improvement: change to argument based input
    except ET.ParseError:
        print("Error: Parse XML failed, skipping", inputXml)
        logHelper.errorLog(inputXml)
        return -1
    root = tree.getroot()

    output = {}
    output["fullText"] = ""
    output["content"] = []

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
                output["content"].append(lineContent)
            else:
                output["content"][-1] = xmlToJsonHelper.updateText(output["content"][-1], lineContent)
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
    opts, args = getopt.getopt(argv, "chi:")
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
    if not opts:
        target_dir = os.path.join(projectPath, config.defaultDir)
        logHelper.logHeader()
        parseFolder(target_dir)
