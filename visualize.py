import streamlit as st
import os
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

def parse_pascal_voc(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    objects = []

    for obj in root.findall('object'):
        obj_dict = {
            'name': obj.find('name').text,
            'bbox': [float(obj.find('bndbox/xmin').text),
                     float(obj.find('bndbox/ymin').text),
                     float(obj.find('bndbox/xmax').text),
                     float(obj.find('bndbox/ymax').text)],
            'element': obj
        }
        confidence_elem = obj.find('conf')
        if confidence_elem is not None:
            obj_dict['confidence'] = float(confidence_elem.text)
        objects.append(obj_dict)

    return objects, tree

def draw_annotations(image_path, annotations, selected_idx, confidence_threshold):
    img = Image.open(image_path).convert('RGB')
    draw = ImageDraw.Draw(img)

    for idx, ann in enumerate(annotations):
        if 'confidence' in ann and ann['confidence'] < confidence_threshold:
            continue
        bbox = ann['bbox']
        outline_color = 'blue' if idx == selected_idx else 'yellow'
        
        box_width = 4  # Increase the width of the bounding box
        draw.rectangle([bbox[0], bbox[1], bbox[2], bbox[3]], outline=outline_color, width=box_width)
        
        draw.text((bbox[0], bbox[1]), ann['name'], fill=outline_color, font=ImageFont.load_default(), font_size=20)

    return img

def delete_annotation(annotation, xml_tree):
    root = xml_tree.getroot()
    root.remove(annotation['element'])

def main():
    st.title("Image Annotation Viewer and Editor")

    st.sidebar.header("Select Directories")

    image_directory = st.sidebar.text_input("Enter image directory path:")
    xml_directory = st.sidebar.text_input("Enter XML directory path:")

    if not os.path.exists(image_directory):
        st.sidebar.write("Image directory path does not exist.")
        return
    if not os.path.exists(xml_directory):
        st.sidebar.write("XML directory path does not exist.")
        return

    # Load image and XML files
    image_files = [f for f in os.listdir(image_directory) if f.lower().endswith(('.jpg', '.jpeg', '.png','.JPG'))]
    xml_files = [f for f in os.listdir(xml_directory) if f.lower().endswith('.xml')]

    if not image_files or not xml_files:
        st.sidebar.write("No image or XML files found in the selected directories.")
        return

    # Match image and XML files by name (without extensions)
    image_xml_pairs = []
    for image_file in image_files:
        image_name, _ = os.path.splitext(image_file)
        corresponding_xml = image_name + ".xml"
        if corresponding_xml in xml_files:
            image_xml_pairs.append((image_file, corresponding_xml))

    if not image_xml_pairs:
        st.sidebar.write("No matching image and XML pairs found.")
        return

    # Sort pairs by image name
    image_xml_pairs.sort()

    # Slider to select pair index
    idx = st.sidebar.slider("Select pair index:", 0, len(image_xml_pairs) - 1, 0)

    # Confidence threshold slider
    confidence_threshold = st.sidebar.slider("Confidence Threshold:", 0.0, 1.0, 0.5)  

    # Get selected image and XML paths
    image_path = os.path.join(image_directory, image_xml_pairs[idx][0])
    xml_path = os.path.join(xml_directory, image_xml_pairs[idx][1])

    # Parse XML annotations
    annotations, xml_tree = parse_pascal_voc(xml_path)

    # Radio buttons to select bounding box
    selected_idx = st.sidebar.radio("Select bounding box:", range(len(annotations)))

    if selected_idx is None:
        st.sidebar.write("Please select a bounding box from the list.")
    else:
        # Draw annotations on the image
        annotated_image = draw_annotations(image_path, annotations, selected_idx, confidence_threshold)
        st.image(annotated_image, caption="Annotated Image", use_column_width=True)
        st.write(f"Image Name: {image_xml_pairs[idx][0]}")  # Display the image name

        # Delete selected bounding box
        if st.button("Delete Selected Bounding Box"):
            delete_annotation(annotations[selected_idx], xml_tree)
            annotations.pop(selected_idx)

            # Save the modified XML file
            xml_tree.write(xml_path)

            st.success("Selected bounding box deleted.")

        # Delete the entire image and XML pair
        if st.button("Delete Image and XML Pair"):
            os.remove(image_path)
            os.remove(xml_path)
            st.success("Image and XML pair deleted.")

    # Display annotations
    st.write("Annotations:")
    if annotations:
        for idx, ann in enumerate(annotations):
            confidence_info = f", Confidence: {ann['confidence']}" if 'confidence' in ann else ""
            st.write(f"{idx + 1}. Class: {ann['name']}, BBox: {ann['bbox']}{confidence_info}")
    else:
        st.write("No annotations found.")

if __name__ == "__main__":
    main()
