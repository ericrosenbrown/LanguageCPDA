from sklearn.cluster import KMeans
import numpy as np
import gensim, logging

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

#TRAIN ON SENTENCES
ss = ['drawing a','drawing b','drawing c','drawing b','drawing a', 'write a', 'write b', 'write c']
test_ss = ['write a']
sentences = []
for sentence in ss:
    t = sentence.split(' ')
    sentences.append(t)
print sentences

#model = gensim.models.Word2Vec(sentences, min_count=1, size=2)
#model = gensim.models.KeyedVectors.load_word2vec_format('/Users/ericrosen/Downloads/GoogleNews-vectors-negative300.bin', binary=True)  
model = gensim.models.Word2Vec.load_word2vec_format('path-to-vectors.txt', binary=False)


#CLUSTER WORDS IN DATABASE
#get all words
words = [] #string of unique word in database
words_vec = [] #word2vec embeding of word
for sentence in sentences:
    for word in sentence:
        if word not in words:
            words.append(word)
            words_vec.append(model[word])

print model.wv['a']
print words_vec[0]

X = np.array([[1, 2],[1, 4],[1,0]])
kmeans = KMeans(n_clusters=5, random_state=0).fit(words_vec)
print words
print kmeans.labels_
kmeans.cluster_centers_
#print model.wv['write']
#print model.wv['a']
