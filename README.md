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
│   └── eda.py
│
├── OUTPUT/
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
### Step 1.5: Install Git LFS (Required for Data Files)

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
initializing Git LFS 
```bash
git lfs install
```
Download Dataset files
```bash
git lfs pull
```

### Step 2: Create a Virtual Environment

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate the virtual environment:

**Mac/Linux**
```bash
source venv/bin/activate
```

**Windows**
```bash
venv\Scripts\activate
```

---

### Step 3: Install Packages

**Base Packages (Required)**

These packages are required to run data preprocessing and exploratory data analysis:

```bash
pip install pandas matplotlib numpy
```

---

### Step 4: Run Data Cleaning and Exploratory Data Analysis Script

First, generate the cleaned dataset:

```bash
python SCRIPTS/data_cleaning.py
```

Generate EDA plots:

```bash
python SCRIPTS/eda.py --coverage --rent-growth-dist --business-dist --scatter
```
