from sklearn.cluster import KMeans
import numpy as np
import gensim, logging

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

#TRAIN ON SENTENCES
ss = ['drawing a b c','drawing b d e','drawing c a b','drawing d c b','drawing ea a e']
sentences = []
for sentence in ss:
    t = sentence.split(' ')
    sentences.append(t)
print sentences

#sentences = [['first', 'sentence'], ['second', 'sentence']]
# train word2vec on the two sentences
model = gensim.models.Word2Vec(sentences, min_count=1, size=2)

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
kmeans = KMeans(n_clusters=2, random_state=0).fit(words_vec)
print words
print kmeans.labels_
print kmeans.predict([[0, 0], [4, 4]])
kmeans.cluster_centers_
