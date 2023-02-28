# ReactIE-PDF-Conversion
This is the PDF converter for ReactIE project. The program takes in a PDF of chemistry paper and outputs a json file containing all the text information, parsed into corresponding sections. See [copper_acetate.json](/Thrust1CheckpointJSON/Copper_Acetate.json) as an example.

## Dependency
This project depends on [zanibbi/SymbolScraper](https://github.com/zanibbi/SymbolScraper), which is packaged as a submodule.

To initialize submodule, first run `git submodule update --init` inside SymbolScraper directory. Then, run `make` to build the package.

Once compiled successfully, an executable will be generated at SymbolScraper/bin/sscraper.

## Usage
There are two ways of running this PDF converter. 

The first way is simply runnig `python3 xmlParser.py`. This will parse all the PDFs inside [Thrust1CheckpointPDF](/Thrust1CheckpointPDF) directory. 

The second way is running `python3 xmlParser.py -i /path/to/pdf`. This only parses the PDF specified. 

If successful, a .json file with all the text information will be generated at [result](/result) directory.

## Issues
- Currently designed to work well with most modern conference papers, but not all format of conference papers are supported.  

