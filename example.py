from pdf2text.generalParser import parseFile

pdfPath = "copper_acetate.pdf"

result = parseFile(pdfPath)

print(result)
