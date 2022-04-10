import pickle
import os
import re
import nltk
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem import PorterStemmer

modelPath = os.path.join(os.path.dirname(__file__), 'svm_model.pkl')
with open(modelPath, 'rb') as f:
    model = pickle.load(f)
ps = PorterStemmer()
stopwords_list = nltk.corpus.stopwords.words('english')


def process_text(x):
    x = re.sub('[^a-zA-Z]', ' ', x).lower().split()
    x = ' '.join([ps.stem(word) for word in x if word not in stopwords_list])
    x = re.sub(r'http\S+\s*', ' ', x)
    x = re.sub('RT|cc', ' ', x)
    x = re.sub(r'#\S+', '', x)
    x = re.sub(r'@\S+', '  ', x)
    x = re.sub(r'[%s]' % re.escape(r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), ' ', x)
    x = re.sub(r'[^\x00-\x7F]', r' ', x)
    x = re.sub(r'\b\w\b''', '', x)
    x = re.sub(r'\s+', ' ', x)
    return x


resume_dataset = os.path.join(os.path.dirname(__file__), 'job_resumes.csv')
df = pd.read_csv(resume_dataset)
tfidf = TfidfVectorizer(sublinear_tf=True, max_features=1500, ngram_range=(1, 1), min_df=0.01, max_df=0.8)
X = tfidf.fit_transform(df['Resume'])

encoder = LabelEncoder()
encoder_classes_path = os.path.join(os.path.dirname(__file__), 'classes.npy')
encoder.classes_ = np.load(encoder_classes_path, allow_pickle=True)


def classify_resume(resume):
    print(resume)
    preprocessed_resume = process_text(resume)
    tfidf_resume = tfidf.transform([preprocessed_resume])
    predicted_class = model.predict(tfidf_resume)[0]
    predicted_class_name = encoder.inverse_transform([predicted_class])
    return predicted_class_name[0]

