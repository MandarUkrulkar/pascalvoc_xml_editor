# XML Class Tool with EDA and Classification Dataset Generator

This Streamlit app provides tools to:
- Explore classes in Pascal VOC XML files
- Replace class names in XML files
- Copy XML files that contain selected classes
- Generate a classification dataset by cropping image objects

## Features

### 1. Class Name Changer
Update class names in all XML files under a specified directory.

### 2. Exploratory Data Analysis (EDA)
Displays class distribution using the XML annotations.

### 3. XML Filter and Copy
Select specific classes and copy XML files containing only those classes to another folder.

### 4. Classification Dataset Generator
Generate a dataset of cropped images from annotated bounding boxes with optional margin.

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Input

- XML files (Pascal VOC format)
- JPEG images associated with the XML files

## Output

- Updated XML files
- Filtered XML annotations
- Cropped classification dataset organized by class folders
