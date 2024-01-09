from pdf2text.generalParser import parseFile

pdfPath = "copper_acetate.pdf"

result = parseFile(pdfPath)
fullText = result['fullText']
contents = result['contents']

print(fullText)
print(contents)
