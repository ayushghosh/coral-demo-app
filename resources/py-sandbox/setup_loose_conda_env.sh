#!/bin/zsh
conda create --name py-loose --file requirements_loose.txt -c conda-forge -y;
conda activate py-loose;
python -m ipykernel install --user --name py-loose --display-name "py-loose";