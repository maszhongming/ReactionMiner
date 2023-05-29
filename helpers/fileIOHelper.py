import os
import json
import shutil

def outputJsonFile(xmlPath, output):
    outputFileName = xmlPath.split("/")[-1][:-4] + ".json"
    path = os.getcwd()
    result_directory = path + "/result/"
    if not os.path.exists(result_directory):
        os.mkdir(result_directory)
    outputFileName = result_directory + outputFileName
    with open(outputFileName, "w") as outfile:
        json.dump(output, outfile, indent=4)
    print("Parsed pdf successfully written to", outputFileName)

# given a path, make sure the path is valid (rename if needed)
# valid path is returned
def validateFilename(inputfile: str):
    newFilename = inputfile.replace(" ", "_").replace("(", "_").replace(")", "_")
    os.rename(inputfile, newFilename)
    return newFilename

# clear everything in the xml and result folder
def cleanFolders():
    path = os.getcwd()
    xml_directory = path + "/xmlFiles/"
    result_directory = path + "/result/"
    if os.path.exists(xml_directory):
        shutil.rmtree(xml_directory)
    if os.path.exists(result_directory):
        shutil.rmtree(result_directory)
