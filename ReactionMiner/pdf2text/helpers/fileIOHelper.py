import json
import os
import shutil

projectPath = os.path.dirname(os.path.abspath(__file__)) + "/../"


def outputDirtyJsonFile(filename, output):
    outputFileName = filename + ".json"
    rawJsonDirPath = projectPath + "/parsed_raw/"
    if not os.path.exists(rawJsonDirPath):
        os.mkdir(rawJsonDirPath)
    outputFilePath = rawJsonDirPath + outputFileName
    with open(outputFilePath, "w") as outfile:
        json.dump(output, outfile, indent=4, ensure_ascii=False)
    print("Raw JSON written to:", outputFilePath)
    return outputFilePath


def outputCleanJsonFile(filename, output):
    outputFileName = filename + ".json"
    result_directory = projectPath + "/results/"
    if not os.path.exists(result_directory):
        os.mkdir(result_directory)
    outputFilePath = result_directory + outputFileName
    with open(outputFilePath, "w") as outfile:
        json.dump(output, outfile, indent=4, ensure_ascii=False)
    print("Clean JSON file written to:", outputFilePath)
    return outputFilePath


def validateFilename(inputfile: str):
    # given a path, make sure the path is valid (rename if needed)
    # valid path is returned
    newFilename = inputfile.replace(" ", "_").replace("(", "_").replace(")", "_")
    os.rename(inputfile, newFilename)
    return newFilename


def cleanFolders():
    # clear everything in the xml and result folder
    xml_directory = projectPath + "/xmlFiles/"
    result_directory = projectPath + "/parsed_raw/"
    final_result_directory = projectPath + "/results/"
    logPath = projectPath + '/log.txt'
    errorLogPath = projectPath + '/errorLog.txt'
    if os.path.exists(xml_directory):
        shutil.rmtree(xml_directory)
    if os.path.exists(result_directory):
        shutil.rmtree(result_directory)
    if os.path.exists(final_result_directory):
        shutil.rmtree(final_result_directory)
    if os.path.exists(logPath):
        os.remove(logPath)
    if os.path.exists(errorLogPath):
        os.remove(errorLogPath)
