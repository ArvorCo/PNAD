# Project Overview

This project is a data analysis pipeline for the PNAD Contínua survey from IBGE (Brazilian Institute of Geography and Statistics). The main goal is to process the raw microdata, clean it, and perform calculations to determine the distribution of the population across different income brackets, based on the Brazilian minimum wage.

The project uses a series of Python scripts to create a reproducible data pipeline. It includes functionalities for:

*   Parsing fixed-width microdata files using a SAS layout definition.
*   Extracting and decoding variables using an Excel data dictionary.
*   Adjusting income values to a common date (Net Present Value) using the IPCA index as a deflator.
*   Performing data quality checks and validations.
*   Aggregating individual-level data to the household level.

The core of the project is a command-line interface (`pnadc_cli.py`) that orchestrates the entire data processing workflow.

## Building and Running

The project is written in Python and its dependencies are listed in the `requirements.txt` file.

### Setup

1.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the pipeline

The main entry point for the project is the `pnadc_cli.py` script. It provides several commands for processing the data. Here is a typical workflow:

1.  **Fetch the latest IPCA data:**
    ```bash
    python scripts/fetch_ipca.py --out data/ipca.csv
    ```

2.  **Extract data from the fixed-width files:**
    ```bash
    python scripts/pnadc_cli.py fwf-extract input_PNADC_trimestral.sas PNADC_012025.txt > data/base_extracted.csv
    ```

3.  **Join with code tables to get labels:**
    ```bash
    python scripts/pnadc_cli.py join-codes data/base_extracted.csv --codes-dir data > data/base_labeled.csv
    ```

4.  **Apply NPV deflators to income columns:**
    ```bash
    python scripts/npv_deflators.py apply --in data/base_labeled.csv --out data/base_labeled_npv.csv --ipca-csv data/ipca.csv --target 2025-07 --min-wage 1518
    ```

### Running Tests

The project uses `pytest` for testing. To run the tests, execute the following command:

```bash
pytest -q
```

## Development Conventions

*   **Code Style:** The project uses `black` for code formatting and `ruff` for linting.
*   **Testing:** Tests are located in the `tests` directory and follow the `test_*.py` naming convention.
*   **Data:** Raw data is expected to be in the root directory, and processed data is stored in the `data` directory.
*   **Notebooks:** The `notebooks` directory contains Jupyter notebooks for exploratory data analysis.
