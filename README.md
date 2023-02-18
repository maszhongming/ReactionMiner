# ReactIE-PDF-Conversion
This is the PDF converter for ReactIE project. The program takes in a PDF of chemistry paper and outputs a json file containing all the text information, parsed into corresponding sections. See [copper_acetate.json](/copper_acetate.json) as an example.

## Dependency
This project depends on [zanibbi/SymbolScraper](https://github.com/zanibbi/SymbolScraper). Once compiled successfully, an executable called sscraper will be generated.

## Usage
First, generate xml file from zanibbi/SymbolScraper. In project directory run `./path_to_sscraper ./path_to_pdf ./`.

Then, change the xmlPath variable in xmlParser.py to your generated xml file. 

Lastly, in terminal run `python xmlParser.py`. If successful, a sample.json file with all the text information will be generated.

## Issues
- Currently designed to work well with The Journal of Organic Chemistry
- Can't extract abstract section yet (next step)
