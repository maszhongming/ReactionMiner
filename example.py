from pdf2text.generalParser import parseFile
from segmentation.segmentor import TopicSegmentor

# pdf2text
pdfPath = "copper_acetate.pdf"

result = parseFile(pdfPath)
fullText = result['fullText']
contents = result['contents']

print(fullText)
print(contents)

# segmentation
with open('./Keywords.txt') as f:
    kws = f.readlines()
keyword = [kw.strip() for kw in kws]

segmentor = TopicSegmentor(device='cuda:0', keywords=keyword)
res = segmentor.segment(contents)

for r_id, r in enumerate(res):
    print("++++++" + str(r_id)+ "++++++")
    print(" ".join(r))
    print("\n")