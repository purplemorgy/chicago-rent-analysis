# chicago-rent-analysis

### Software Used
- Python (version 3.9 or higher)

### Python Packages Required

The following packages must be installed:

- pandas  
- matplotlib  
- numpy

### Platform

This project was developed and tested on macOS.  
It should also run on Windows or Linux with the same Python setup.

## Section 2: Map of the Documentation

Project Folder Structure:

```
chicago-rent-analysis/
│
├── DATA/
│   ├── Business_Licenses_Chicago.csv
│   ├── cleaned_chicago_dataset.csv
│   └── Zillow_Rent_Prices.csv
│
├── SCRIPTS/
│   ├── data_cleaning.py
│   ├── eda.py
│   ├── panel_regression.py
│   └── run_pipeline.sh
│
├── OUTPUT/
│   ├── business_openings_distribution.png
│   ├── business_vs_rent_growth.png
│   ├── rent_and_business_monthly_XXXXX.png
│   ├── rent_data_availability.png
│   └── rent_growth_distribution.png
│
├── README.md
└── LICENSE
```
## Section 3: Instructions for Reproducing Results

### Step 1: Clone the Repository

```bash
git clone https://github.com/purplemorgy/chicago-rent-analysis
cd chicago-rent-analysis
```

---
### Step 2: Install Git LFS (Required for Data Files)

This project uses Git Large File Storage (LFS) to manage large `.csv` datasets.  
Without Git LFS, the data files will not download correctly.

#### Install Git LFS

**Mac (Homebrew):**
```bash
brew install git-lfs
```

**windows**
download from https://git-lfs.com/

**Linux**
```bash
sudo apt install git-lfs
```
**Initializing Git LFS**
```bash
git lfs install
```
**Download Dataset files**
```bash
git lfs pull
```

### Step 3: Run the pipeline

This project includes a pipeline script that automatically:

- Creates a virtual environment

- Installs required Python packages

- Runs data cleaning

- Generates EDA plots

- Runs panel regression models and prints interpretations

```bash
bash run_pipeline.sh
```
