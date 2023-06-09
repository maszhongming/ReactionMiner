
# given a path to an xml file, modify the file to make it a valid xml file
def preParseXML(path):
    with open(path, "r") as file:
        filedata = file.read()
    # replace all invalid xml characters with valid ones
    filedata = filedata.replace(">&<", ">&amp;<")
    filedata = filedata.replace("><<", ">&lt;<")
    filedata = filedata.replace(">><", ">&gt;<")
    filedata = filedata.replace(chr(0), "")
    filedata = filedata.replace("", "")
    # remove all ascii characters that are not tab, newline, or carriage return
    for invalidAscii in range(1, 31):
        if invalidAscii == 9 or invalidAscii == 10 or invalidAscii == 13:
            continue   # tab, newline, carriage return 
        char = chr(invalidAscii)
        filedata = filedata.replace(char, "")
    # write the modified xml file back to the original path
    with open(path, "w") as file:
        file.write(filedata)