import xml.etree.ElementTree as ET
tree = ET.parse('./LearningNavigationInstructions/data/Paragraph.xml')
root = tree.getroot()
for child in root:
    print child.tag, child.attrib
    for neighbor in child:
        print neighbor
        print neighbor.text
        print neighbor.tag
