# ReactIE-PDF-Conversion

This is the PDF converter for ReactIE project. The program takes in a PDF of chemistry paper and outputs a json file containing all the text information, parsed into corresponding sections. See any .json file in parsed_postprocess folder, such as this one: [acs.accounts.3c00129.json](/example_journals_results/acs.accounts.3c00129.json) generated from this pdf: [acs.accounts.3c00129.pdf](/example_journals/acs.accounts.3c00129.pdf) as an example.

## Dependency

This project depends on [zanibbi/SymbolScraper](https://github.com/zanibbi/SymbolScraper), which is packaged as a submodule.

To initialize submodule, first run `git submodule update --init` inside SymbolScraper directory. Then, run `make` to build the package.

Once compiled successfully, an executable will be generated at SymbolScraper/bin/sscraper.

## Usage

To run the program against the provided example journals, run `python3 generalParser.py`. This will parse all the PDFs inside the directory specified in [config.py](/config.py), which defaults to [example_journals](/example_journals).

To parse a specific folder, first change the directory in [config.py](/config.py) to the desired folder, then run `python3 generalParser.py`.

To parse a specific PDF, run `python3 generalParser.py -i /path/to/pdf`. 

After the program finishes, the resulting json files will be generated at [results](/results) directory.

To clean the results and xmlFiles directory, run `python3 generalParser.py -c`.

If the parser doesn't generate a json file with expected paragraph format, try changing the constants such as tabwidth and lineheight in [config.py](/config.py).
