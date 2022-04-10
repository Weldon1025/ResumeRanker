from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem import PorterStemmer
import nltk
import re
import os
import pandas as pd


ps = PorterStemmer()
nltk.download('stopwords')
stopwords_list = nltk.corpus.stopwords.words('english')

resume_dataset = os.path.join(os.path.dirname(__file__), 'job_resumes.csv')
df = pd.read_csv(resume_dataset)

tfidf = TfidfVectorizer(sublinear_tf=True, max_features=1500, ngram_range=(1, 1), min_df=0.01, max_df=0.8)
X = tfidf.fit_transform(df['Resume'])


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


def get_cosine_sim(resume_text, job_description):
    resume_text = process_text(resume_text)
    job_description = process_text(job_description)
    tfidf_resume = tfidf.transform([resume_text])
    tfidf_job = tfidf.transform([job_description])
    texts = [tfidf_resume, tfidf_job]
    similarity = cosine_similarity(texts[0], texts[1])
    percentage = round(similarity[0][0] * 100, 2)
    return percentage

