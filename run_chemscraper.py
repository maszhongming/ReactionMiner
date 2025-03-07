import logging
import os
import requests
import sys
from typing import BinaryIO
from io import BytesIO

from chemscraper.fast_api_client import Client
from chemscraper.fast_api_client.types import File
from chemscraper.fast_api_client.api.default import index_pdfs_reactions_batch_index_pdfs_reactions_batch_post as index_pdfs_reactions_batch
from chemscraper.fast_api_client.api.default.index_pdfs_reactions_batch_index_pdfs_reactions_batch_post import BodyIndexPdfsReactionsBatchIndexPdfsReactionsBatchPost as IndexPdfsReactionsBatchPostBody

logging.basicConfig(
    format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG
)
logger = logging.getLogger('run_chemscraper')

# Path to input PDFs for RM+CS
# Files in this path will be automatically downloaded from MinIO before running the AlphaSynthesis job
CHEMSCRAPER_PDF_INPUT_DIR = os.environ.get('CHEMSCRAPER_PDF_INPUT_DIR', '/workspace/10test')

# Path to output JSONs from ReactionMiner
# Files in this path will be automatically uploaded to MinIO after running the AlphaSynthesis job
CHEMSCRAPER_REACTIONMINER_JSON_DIR = os.environ.get('CHEMSCRAPER_REACTIONMINER_JSON_DIR', '/workspace/extraction/results_filtered')

# Path to output from full RM+CS workflow
# We store to the same path as ReactionMiner outputs, so that this is also uploaded to MinIO
CHEMSCRAPER_OUTPUT_DIR = os.environ.get('CHEMSCRAPER_OUTPUT_DIR', CHEMSCRAPER_REACTIONMINER_JSON_DIR)

# A unique string identifier for this searchable index
# Used when submitting to the /search endpoint
CHEMSCRAPER_INDEX_NAME = os.environ.get('CHEMSCRAPER_INDEX_NAME', os.environ.get('JOB_ID', 'test'))

# Base URL to ChemScraper API
# We will override this default in production
CHEMSCRAPER_BASE_URL = os.environ.get('CHEMSCRAPER_BASE_URL', 'http://chemscraper-services-staging.staging.svc.cluster.local:8000')

# Read PDFs + locate matching JSONs on disk
# Create a mapping of PDF file -> JSON file
def parse_input_files(pdf_input_dir):
    # Loop to build up CSV mapping and file lists
    mapping = {}
    pdf_files = []
    json_files = []

    # Walk input PDF directory looking for PDF files
    for root, _, files in os.walk(pdf_input_dir):
        logger.info(f"Current directory: {root}")
        for file in files:
            # Skip non-PDF files
            if not file.endswith(".pdf"):
                logger.debug(f"  Skipping non-PDF File: {file}")
            else:
                # If a PDF is found, check for a matching JSON file
                pdf_file_name = file
                logger.info(f"  PDF File: {pdf_file_name}")
                pdf_file_path = os.path.join(root, file)
                json_file_name = pdf_file_name.replace('.pdf', '.json')
                json_file_path = os.path.join(CHEMSCRAPER_REACTIONMINER_JSON_DIR, json_file_name)

                # Skip processing PDFs where no matching JSON is found
                if not os.path.exists(json_file_path):
                    logger.warning(f"  No matching JSON file found: {file}")
                else:
                    # For each matching PDF-JSON pair, add to CSV mapping
                    logger.info(f"  Matching JSON file found: {json_file_name}")

                    # Maintain lists of these pairs to submit at the end
                    mapping[pdf_file_name] = json_file_name
                    pdf_files.append(pdf_file_path)
                    json_files.append(json_file_path)

        logger.debug('PDF Files: ' + str(pdf_files))
        logger.debug('JSON Files: ' + str(json_files))
        logger.debug('Mapping: ' + str(mapping))

        # Return lists of files and CSV mapping
        return pdf_files, json_files, mapping


# Write mapping.csv to file, and submit this file with our request
def save_mapping_csv(file_path, mapping):
    index = 0
    with open(file_path, 'w') as f:
        # Write CSV headers - this is important
        f.write(f'id,pdf_name,json_name\n')
        for pdf_file in mapping:
            # Read mapping to write CSV line by line
            json_file = mapping[pdf_file]
            f.write(f'{index},{pdf_file},{json_file}\n')
            index += 1

# Submit mapping + related files to Chemscraper API
def submit_to_chemscraper(index_name, pdf_files, json_files, mapping):
    # Save mapping.csv to disk, upload to MinIO later
    mapping_csv_file_path = os.path.join(CHEMSCRAPER_REACTIONMINER_JSON_DIR, 'mapping.csv')
    save_mapping_csv(file_path=mapping_csv_file_path, mapping=mapping)

    # Create a new ChemScraper API client and submit the
    # PDF + JSON files and the mapping that links them
    with Client(base_url=CHEMSCRAPER_BASE_URL) as client:
        return index_pdfs_reactions_batch.sync(client=client, index_name=index_name, body=IndexPdfsReactionsBatchPostBody(
            # Our list of ReactionMiner PDF inputs
            pdf_files=[File(
                file_name=file.split('/')[-1],
                payload=read_file_bytes(os.path.join(CHEMSCRAPER_PDF_INPUT_DIR, file)),
                mime_type='application/pdf'
            ) for file in pdf_files],

            # Our list of ReactionMiner JSON outputs
            json_reaction_files=[File(
                file_name=file.split('/')[-1],
                payload=read_file_bytes(os.path.join(CHEMSCRAPER_REACTIONMINER_JSON_DIR, file)),
                mime_type='application/json'
            ) for file in json_files],

            # The CSV created earlier that maps PDF file -> JSON file
            mapping_file=File(
                file_name='mapping.csv',
                payload=read_file_bytes(os.path.join(CHEMSCRAPER_REACTIONMINER_JSON_DIR, 'mapping.csv')),
                mime_type='text/csv'
            ),
        ))

# TODO: Read large files in chunks?
def read_file_bytes(path) -> BinaryIO:
    with open(path, mode='rb') as f:
        return BytesIO(f.read())


# Write ChemScraper JSON response to file
def write_json_output(output_file_path):
    logger.info(f'Writing response to file: {output_file_path}')
    with open(output_file_path, "w") as f:
        f.write(str(response))

# Walk directory and build up a mapping to submit to ChemScraper
# exit with error code = 1 if any error encountered
# (error code = 0 indicates success)
if __name__ == "__main__":
    logger.info(f'Submitting these files to ChemScraper')
    logger.info(f'  Index Name: {CHEMSCRAPER_INDEX_NAME}')
    logger.info(f'  PDF  Input Dir: {CHEMSCRAPER_PDF_INPUT_DIR}')
    logger.info(f'  JSON Input Dir: {CHEMSCRAPER_REACTIONMINER_JSON_DIR}')
    logger.info(f'  Output Dir: {CHEMSCRAPER_OUTPUT_DIR}')

    try:
        pdf_files, json_files, mapping = parse_input_files(pdf_input_dir=CHEMSCRAPER_PDF_INPUT_DIR)
        response = submit_to_chemscraper(index_name=CHEMSCRAPER_INDEX_NAME, pdf_files=pdf_files, json_files=json_files, mapping=mapping)

        # Write JSON response to file
        if response is not None:
            logger.debug("Response: " + str(response))
            output_file_path = os.path.join(CHEMSCRAPER_OUTPUT_DIR, 'chemscraper-output.json')
            write_json_output(output_file_path=output_file_path)
        else:
            # Raise error status if no response body
            response.raise_for_status()
    except Exception as ex:
        logger.error(f'ERROR: {ex}')
        sys.exit(1)
