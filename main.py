import os
import xml.etree.ElementTree as ET
import streamlit as st
import pandas as pd
import shutil
from PIL import Image

def get_existing_classes(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Collect existing class names
    existing_classes = set()
    for obj_elem in root.findall(".//object"):
        name_elem = obj_elem.find("name")
        if name_elem is not None:
            existing_classes.add(name_elem.text)

    return list(existing_classes)

def change_class_names(xml_file, old_class_names, new_class_name):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Iterate through all "object" elements
    for obj_elem in root.findall(".//object"):
        # Find the "name" element under each "object"
        name_elem = obj_elem.find("name")

        # Update the "name" element text if it matches any of the old class names
        if name_elem is not None and name_elem.text in old_class_names:
            name_elem.text = new_class_name

    # Save the modified XML
    tree.write(xml_file)

def create_eda_dataframe(dir_path):
    eda_data = {}

    for filename in os.listdir(dir_path):
        if filename.endswith(".xml"):
            xml_file_path = os.path.join(dir_path, filename)
            existing_classes = get_existing_classes(xml_file_path)

            for class_name in existing_classes:
                if class_name not in eda_data:
                    eda_data[class_name] = 0

            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            for obj_elem in root.findall(".//object"):
                name_elem = obj_elem.find("name")
                if name_elem is not None:
                    class_name = name_elem.text
                    eda_data[class_name] += 1

    unique_classes = list(eda_data.keys())
    total_counts = list(eda_data.values())

    # Calculate percentages
    total_objects = sum(total_counts)
    percentages = [count / total_objects * 100 for count in total_counts]

    return pd.DataFrame({"Class": unique_classes, "Total Count": total_counts, "Percentage": percentages})

def copy_xml_to_folder(dir_path, output_folder, selected_classes_for_copy):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(dir_path):
        if filename.endswith(".xml"):
            xml_file_path = os.path.join(dir_path, filename)
            output_xml_file_path = os.path.join(output_folder, filename)

            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            # Create a new XML tree
            new_root = ET.Element("annotation")

            # Copy initial elements from the original XML
            for elem in root:
                if elem.tag != "object":
                    new_root.append(elem)

            # Copy selected object elements
            for obj_elem in root.findall(".//object"):
                name_elem = obj_elem.find("name")
                if name_elem is not None and name_elem.text in selected_classes_for_copy:
                    new_root.append(obj_elem)

            # Check if any selected classes are found in the XML
            if len(new_root.findall(".//object")) > 0:
                new_tree = ET.ElementTree(new_root)
                new_tree.write(output_xml_file_path)

def generate_classification_dataset(image_dir, output_path, xml_dir, selected_classes_for_dataset):
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    for filename in os.listdir(xml_dir):
        if filename.endswith(".xml"):
            xml_file_path = os.path.join(xml_dir, filename)
            image_name = filename[:-4] + ".jpg"
            image_file_path = os.path.join(image_dir, image_name)
            if not os.path.exists(image_file_path):
                continue

            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            # Flag to check if at least one selected class object is found
            class_found = False
            
            for obj_elem in root.findall(".//object"):
                name_elem = obj_elem.find("name")
                if name_elem is not None:
                    class_name = name_elem.text
                    if class_name in selected_classes_for_dataset:
                        class_found = True
                        bbox_elem = obj_elem.find("bndbox")
                        if bbox_elem is not None:
                            xmin = float(bbox_elem.find("xmin").text)
                            ymin = float(bbox_elem.find("ymin").text)
                            xmax = float(bbox_elem.find("xmax").text)
                            ymax = float(bbox_elem.find("ymax").text)

                            # Crop the image based on bounding box
                            # Define the additional crop size (25 pixels more from each side)
                            additional_crop = 50
                            image = Image.open(image_file_path)
                            # Calculate new cropping coordinates
                            xmin_crop = max(0, xmin - additional_crop)
                            ymin_crop = max(0, ymin - additional_crop)
                            xmax_crop = min(image.width, xmax + additional_crop)
                            ymax_crop = min(image.height, ymax + additional_crop)

                            # Crop the image based on modified bounding box
                            cropped_image = image.crop((xmin_crop, ymin_crop, xmax_crop, ymax_crop))

                            # Save the cropped image in respective class folder
                            class_output_path = os.path.join(output_path, class_name)
                            if not os.path.exists(class_output_path):
                                os.makedirs(class_output_path)
                            
                            cropped_image.save(os.path.join(class_output_path, f"{os.path.basename(image_dir)}_{image_name[:-4]}_{class_name}_{int(xmin)}_{int(ymin)}_{int(xmax)}_{int(ymax)}.jpg"))

            
            # Check if any selected class object is found, if not, skip copying
            if not class_found:
                continue
            
            # Copy XML file
            #shutil.copy(xml_file_path, os.path.join(output_path, filename))


def main():
    st.title("XML Class Name Changer, EDA, and XML Copy")

    # Get the directory path containing XML files
    xml_dir = st.text_input("Enter the directory path containing XML files:")
    image_dir = st.text_input("Enter the directory path containing images:")

    # Display a message while fetching existing classes
    with st.spinner("Fetching existing classes..."):
        existing_classes = set()
        for filename in os.listdir(xml_dir):
            if filename.endswith(".xml"):
                xml_file_path = os.path.join(xml_dir, filename)
                existing_classes.update(get_existing_classes(xml_file_path))

    # Display EDA DataFrame
    st.subheader("Exploratory Data Analysis (EDA)")
    eda_dataframe = create_eda_dataframe(xml_dir)
    st.dataframe(eda_dataframe)

    # Allow the user to select multiple old class names from the list
    old_class_names = st.multiselect("Select the classes to replace:", sorted(existing_classes))

    # Get the new class name from the user
    new_class_name = st.text_input("Enter the new class name:")

    if st.button("Change Class Names"):
        # Check if the directory path, old class names, and new class name are provided
        if xml_dir and old_class_names and new_class_name:
            # Iterate over all XML files in the directory
            for filename in os.listdir(xml_dir):
                if filename.endswith(".xml"):
                    xml_file_path = os.path.join(xml_dir, filename)

                    # Call the function to change the class names for each XML file
                    change_class_names(xml_file_path, old_class_names, new_class_name)

                    st.write(f"Class names in {xml_file_path} updated from "
                             f"{old_class_names} to {new_class_name}.")

            st.success("Processing complete.")
        else:
            st.warning("Please provide the directory path, old class names, and new class name.")

    # Get the folder path for copying XML files
    output_folder = st.text_input("Enter the folder path to copy XML files with selected classes:")

    # Allow the user to select classes for copying
    selected_classes_for_copy = st.multiselect("Select classes for copying:", sorted(existing_classes))

    if st.button("Copy XML Files"):
        # Check if the output folder and selected classes for copying are provided
        if output_folder and selected_classes_for_copy:
            # Call the function to copy XML files with selected classes
            copy_xml_to_folder(xml_dir, output_folder, selected_classes_for_copy)

            st.success(f"XML files with selected classes copied to {output_folder}.")

    # Get the output path for saving classification dataset
    classification_output_path = st.text_input("Enter the output path to save classification dataset:")

    # Allow the user to select classes for generating classification dataset
    selected_classes_for_dataset = st.multiselect("Select classes for generating classification dataset:", sorted(existing_classes))

    if st.button("Generate Classification Dataset"):
        # Check if the output path and selected classes for dataset generation are provided
        if classification_output_path and selected_classes_for_dataset:
            # Call the function to generate classification dataset
            generate_classification_dataset(image_dir, classification_output_path, xml_dir,selected_classes_for_dataset)

            st.success("Classification dataset generated and saved successfully.")
        else:
            st.warning("Please provide the output path and select classes for generating classification dataset.")

if __name__ == "__main__":
    main()
