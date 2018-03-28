import xml.etree.ElementTree as ET
import re
import random

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

def train_markov(sentences): #s is a sentence to predict stops on.
    words_dict = {} #keys: words. Values: [number of times followed by stop,number of appeareances]
    for s in sentences:
        s = s.lower()
        stops = s.split(".")
        for fragment in range(len(stops)-1):
            words = stops[fragment].split(" ")
            for word in range(len(words)):
                if word == len(words)-1: #last word, is followed by a stop
                    if words[word] in words_dict.keys(): #already in the dictionary, add 1 to both stops and appearences
                        counter = words_dict[words[word]]
                        counter[0] += 1
                        counter[1] += 1
                        words_dict[words[word]] = counter
                    else: #new, create the entry and add 1 to both
                        words_dict[words[word]] = [1,1]
                else: #not the last word, is followed by another word
                    if words[word] in words_dict.keys(): #already in dict, add 1 to appeareances
                        counter = words_dict[words[word]]
                        counter[1] += 1
                        words_dict[words[word]] = counter
                    else: #completely new, initialize entry with 1 in appeareance
                        words_dict[words[word]] = [0,1]
            #print words
            #print words[-1] 
        #print stops
        #print len(stops)-1
    #print words_dict['right']
    stop_probs = {} #key: words. Values: probabiliy of a stop following the word. Calculated by using words_dict. 
    average_stop_prob = 0
    for word in words_dict.keys():
        counter = words_dict[word]
        prob = float(counter[0])/float(counter[1])
        stop_probs[word] = prob
        average_stop_prob += prob
    average_stop_prob = float(average_stop_prob)/len(words_dict.keys())
    #print average_stop_prob
    return [stop_probs,average_stop_prob]

def predict_marco(): #predict where stops happen
    #get sentence from marco dataset
    p = 18
    data = parse_xml()
    [words_dict, av_prob] = train_markov(data) 
    #print av_prob
    #print words_dict['left']
    sentence =  data[p]
    print "original sentence:",sentence

    pattern = re.compile('([^\s\w]|_)+') #removes everything but words and spaces. 
    clean_sentence = pattern.sub('', sentence)
    clean_sentence = clean_sentence.split(" ")
    #print clean_sentence

    new_sentence = ""
    for word in clean_sentence:
        if word != '' or '\n': #is actually a word
            #print word
            if word in words_dict.keys(): #we've seen it before, use probbility to decide on period or not
                if random.uniform(0,1) <= words_dict[word]: #we predict a stop happens after this word
                    new_sentence += word + ". "
                else: #choose no stop after
                    new_sentence += word + " "
            else: #never seen before, use general probability
                if random.uniform(0,1) <= av_prob: #we predict a stop happens after this word
                    new_sentence += word + ". "
                else: #choose no stop after
                    new_sentence += word + " "
    print "new_sentence:",new_sentence
            
                
    
       


predict_marco()

def test_ss(): #testing stupidstop
    sentences = ["Nakul likes to program.", #1 stop
    "Nakul likes to program. why not. it can be fun.", #1 stop
    "Nakul likes to program. He does it at all the time.", #2 stops 
    "Nakul likes to program. He does it at all the time. He uses a computer! Why you ask? Because it makes the most sense, silly." #5 stops
    ]

    print stupidstop(sentences[1])

#test_ss()

