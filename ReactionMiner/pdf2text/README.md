# PDF-to-Text Conversion

This is the PDF converter in the Reaction Miner System. The module takes in a PDF of chemistry paper and outputs a json file containing all the text information, parsed into corresponding sections.

## Dependency

This module depends on [zanibbi/SymbolScraper](https://github.com/zanibbi/SymbolScraper), which is packaged as a submodule.

To initialize submodule, first run `git submodule update --init` inside SymbolScraper directory. Then, run `make` to build the package.

Once compiled successfully, an executable will be generated at SymbolScraper/bin/sscraper.

## Usage

To parse a specific PDF, run `python3 generalParser.py -i /path/to/pdf`. 

To parse a specific folder, first change the directory in [config.py](config.py) to the desired folder, then run `python3 generalParser.py`.

After the program finishes, the resulting json files will be generated at results/ directory.

To clean the results and xmlFiles directory, run `python3 generalParser.py -c`.

If the parser doesn't generate a json file with expected paragraph format, try changing the constants such as tabwidth and lineheight in [config.py](config.py).
