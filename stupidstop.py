import xml.etree.ElementTree as ET
def parse_xml():
    text_corpus = []
    tree = ET.parse('./LearningNavigationInstructions/data/Paragraph.xml')
    root = tree.getroot()
    for child in root:
        #print child.tag, child.attrib
        for neighbor in child.iter("instruction"):
            #print neighbor
            #print neighbor.text
            #print neighbor.tag
            text_corpus.append(neighbor.text)
    return text_corpus

def stupidstop(s): #s is a sentence to predict stops on.
    s = s.lower()
    stops = s.split(".")
    return len(stops)-1

def predict_marco():
    p = 15
    data = parse_xml()
    print data[p]
    print stupidstop(data[p])

predict_marco()

def test_ss(): #testing stupidstop
    sentences = ["Nakul likes to program.", #1 stop
    "Nakul likes to program. why not. it can be fun.", #1 stop
    "Nakul likes to program. He does it at all the time.", #2 stops 
    "Nakul likes to program. He does it at all the time. He uses a computer! Why you ask? Because it makes the most sense, silly." #5 stops
    ]

    print stupidstop(sentences[1])

#test_ss()

