FROM pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime

# FIXME: Temporary workaround for NFS file permissions issues
USER root

###################
#     pdf2text    #
###################

# Install s2orc
COPY s2orc-doc2json ./s2orc-doc2json

# Setup conda env + doc2json
RUN conda create -n doc2json python=3.8 pytest && conda clean --all -y
SHELL ["conda", "run", "-n", "doc2json", "/bin/bash", "-c"]
WORKDIR /workspace/s2orc-doc2json
RUN pip install -r ./requirements.txt --no-cache-dir
RUN python setup.py develop

# Copy in pdf2text python scripts
WORKDIR /workspace
COPY pdf2text ./pdf2text

###################
#  ReactionMiner  #
###################

WORKDIR /workspace

# Set up conda env
COPY ./environment.docker.yml .
RUN conda env update -n base -f environment.docker.yml && conda clean --all -y

# Install other Python dependencies
RUN conda run -n base python -m spacy download en_core_web_sm

# Add ReactionMiner Python scripts
COPY extraction ./extraction
COPY segmentation ./segmentation

# pdf2text is needed by extraction for config.py
COPY pdf2text/config.py ./extraction/config.py
COPY example.py ./example.py
COPY run_chemscraper.py ./run_chemscraper.py
COPY chemscraper ./chemscraper

# Run our docker entrypoint to execute the full workflow
COPY entrypoint.sh ./entrypoint.sh
CMD [ "./entrypoint.sh" ]
