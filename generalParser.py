import xml.etree.ElementTree as ET
import os
import sys, getopt
import helpers.pdfToXmlHelper as pdfToXmlHelper
import helpers.xmlToJsonHelper as xmlToJsonHelper
import helpers.fileIOHelper as fileIOHelper
import config
from postprocess import cleanJson

# given a path to a pdf file, parse the pdf file and output a json file
# both symbol scraper and xml parser are run
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
        print("Step 1: Parse PDF into XML using Symbol Scraper, written to:", xmlPath)
    # don't parse xml if json already exists
    targetJsonPath = os.getcwd() + "/parsed_raw/" + pdfPath.split("/")[-1][:-4] + ".json"
    if os.path.exists(targetJsonPath):
        print("JSON file already exists")
    else:    
        parse(xmlPath)
    targetCleanJsonPath = os.getcwd() + "/results/" + pdfPath.split("/")[-1][:-4] + ".json"
    if os.path.exists(targetCleanJsonPath):
        print("Clean JSON file already exists")
        return
    else:
        cleanJson(targetJsonPath)
    # clean up useless .md files created by SymbolScraper
    pdfDirPath = os.path.dirname(pdfPath)
    for mdFile in os.listdir(pdfDirPath):
        if mdFile.endswith(".md") and mdFile != "README.md":
            os.remove(pdfDirPath + "/" + mdFile)

# given a path to a folder, recursively parse all pdf files in it
def parseFolder(folderPath: str):
    for item in sorted(os.listdir(folderPath)):
        itemPath = os.path.join(folderPath, item)
        if itemPath.endswith(".pdf"):
            validPath = fileIOHelper.validateFilename(itemPath)
            parseFile(validPath)
        elif os.path.isdir(itemPath):
            validPath = fileIOHelper.validateFilename(itemPath)
            parseFolder(validPath)
        # print()

# given a path to a xml file, parse the xml file and output a json file
def parse(inputXml: str):
    pdfToXmlHelper.preParseXML(inputXml)
    tree = ET.parse(inputXml)  # improvement: change to argument based input
    root = tree.getroot()

    output = {}
    output["fullText"] = ""
    output["content"] = []

    paragraphStart =xmlToJsonHelper.findOffset(root)

    for pageXml in root.iter("Page"):
        prevLineBBOX = None
        for lineXml in pageXml.iter("Line"):
            # building line content
            lineContent = ""
            lineXMLBBOX = lineXml.attrib["BBOX"]
            for wordXml in lineXml.iter("Word"):
                word =xmlToJsonHelper.buildWord(wordXml)
                lineContent =xmlToJsonHelper.updateText(lineContent, word)
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
    fileIOHelper.outputDirtyJsonFile(inputXml, output)

# main function
if __name__ == "__main__":
    argv = sys.argv[1:]
    inputfile = ""
    opts, args = getopt.getopt(argv, "chi:")
    for opt, arg in opts:
        if opt == "-h":
            print("[Usage]: python3 xmlParser.py -i <inputPDF>")
            print("Result will be saved as a .json file in the results/ folder")
            sys.exit()
        elif opt == "-i":
            inputfile = arg
            parseFile(inputfile)
        elif opt == "-c":
            fileIOHelper.cleanFolders()
            # cwd = os.getcwd()
            # target_dir = os.path.join(cwd, config.defaultDir)
            # parseFolder(target_dir)
    if not opts:
        cwd = os.getcwd()
        target_dir = os.path.join(cwd, config.defaultDir)
        parseFolder(target_dir)
