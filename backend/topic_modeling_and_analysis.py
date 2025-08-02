print("Begin Topic Modeling Script")

import sys
import os
import json
import warnings
import re
from pprint import pprint

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import nltk
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.tokenize import word_tokenize
gensim_stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()

from sklearn.decomposition import LatentDirichletAllocation, NMF, TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

from gensim.parsing.preprocessing import STOPWORDS
from gensim.corpora import Dictionary
from gensim.models import LdaModel, CoherenceModel, LsiModel, Nmf

from bertopic import BERTopic
from hdbscan import HDBSCAN
from textblob import TextBlob

from sentence_transformers import SentenceTransformer
from umap import UMAP

import datetime
now = datetime.datetime.now()
date_string = now.strftime("%Y%m%d")

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Check if NLTK data is already downloaded
#nltk_data_path = os.path.join(os.path.expanduser("~"), "nltk_data")
#if not os.path.exists(nltk_data_path):
#    nltk.download('stopwords', quiet=True)
#    nltk.download('punkt', quiet=True)
#    nltk.download('wordnet', quiet=True)
#    nltk.download('punkt_tab', quiet=True)
#    nltk.download('averaged_perceptron_tagger_eng')
#    nltk.download('vader_lexicon')

# ----------------------------
# Step 1: Load the Data
# ----------------------------

# Check if the CSV file path is provided
if len(sys.argv) != 2:
    print("Usage: python topic_modeling_script.py <path_to_csv_file>")
    sys.exit(1)

csv_file = sys.argv[1]

# Read the CSV file into a DataFrame
try:
    df = pd.read_csv(csv_file, chunksize=1000)
except Exception as e:
    print(f"Error reading CSV file: {e}")
    sys.exit(1)

df = pd.concat(df, ignore_index=True)





# Extract conversations
conversations = []
conversations_chosen = []
conversations_rejected = []

for index, row in df.iterrows():
    convo_json = row.get('conversation_json', '{}')
    try:
        convo = json.loads(convo_json)
    except json.JSONDecodeError:
        convo = {}
    chosen = convo.get('chosen') or ''
    neutral = convo.get('neutral') or ''
    rejected = convo.get('rejected') or ''
    text = ' '.join([chosen, neutral, rejected])
    conversations.append(text)
    conversations_chosen.append(chosen)
    conversations_rejected.append(rejected)

df['conversation'] = conversations
df['chosen_conversations'] = conversations_chosen
df['rejected_conversations'] = conversations_rejected
df['num_thumbs_up'] = df['chosen_conversations'].apply(lambda x: x.count("Human:"))
df['num_thumbs_down'] = df['rejected_conversations'].apply(lambda x: x.count("Human:"))

# Regular expression to match everything following 'Human:' and stop before 'Assistant:' or 'Feedback:'
human_pattern = r"Human:(.*?)(?=\n(?:Assistant:|Feedback:|$))"
assistant_pattern = r'Assistant:.*?(?=Human:|Feedback:|$)'
feedback_pattern = r'Feedback:.*?(?=Human:|Assistant:|$)'

import re

# Define the function to apply to the conversation columns
def process_conversation(pattern, label=None):
    return df['conversation'].apply(lambda x: ' '.join(re.findall(pattern, x, re.DOTALL)) if re.findall(pattern, x, re.DOTALL) else ' ').str.replace(f"{label}:", "", regex=False) if label else df['conversation'].apply(lambda x: ' '.join(re.findall(pattern, x, re.DOTALL)) if re.findall(pattern, x, re.DOTALL) else ' ')

# Apply the function to each column
df['human_conversation'] = process_conversation(human_pattern)
df['assistant_conversation'] = process_conversation(assistant_pattern, "Assistant")
df['feedback_conversation'] = process_conversation(feedback_pattern, "Feedback")

import hashlib

def anonymize_email(email):
  """Hashes an email address using SHA-256."""
  encoded_email = str(email).encode('utf-8')
  return hashlib.sha256(encoded_email).hexdigest()

def anonymize_email_column(df, column_name):
  """Anonymizes an email column in a Pandas DataFrame."""
  df[column_name] = df[column_name].apply(anonymize_email)
  return df

df = anonymize_email_column(df, 'email')
df = anonymize_email_column(df, 'user_id')






# ----------------------------
# Step 2: Preprocess the Text
# ----------------------------

def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return None  # for easy if-statement


# def preprocess_text(text):
#     # Ensure the input is a string (handle NaN or None cases)
#     if not isinstance(text, str):
#         text = str(text) if text is not None else ""

#     # Remove non-word characters (punctuation, etc.)
#     cleaned_text = re.sub(r'[^\w\s]', '', text)

#     stop_words = set(gensim_stop_words)
#     words = word_tokenize(cleaned_text.lower())
#     filtered_words = [word for word in words if word not in stop_words and len(word) >= 4]  # remove words with less than 4 characters

#     # Apply stemming
#     stemmed_words = [stemmer.stem(word) for word in filtered_words]

#     tagged = nltk.pos_tag(stemmed_words)
#     tokens_rtn = []
#     for stemmed_word, tag in tagged:
#         wntag = get_wordnet_pos(tag)
#         if wntag is None:
#             tkn = lemmatizer.lemmatize(stemmed_word)
#         else:
#             tkn = lemmatizer.lemmatize(stemmed_word, pos=wntag)
#         tokens_rtn.append(tkn)

#     return ' '.join(tokens_rtn)

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

def preprocess_text(text):
    # Ensure the input is a string (handle NaN or None cases)
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    cleaned_text = re.sub(r'[^\w\s]', '', text)
    words = word_tokenize(cleaned_text.lower())
    filtered_words = [lemmatizer.lemmatize(word) for word in words if word not in ENGLISH_STOP_WORDS and len(word) >= 4]
    return ' '.join(filtered_words)

from joblib import Parallel, delayed

def parallel_preprocess(text):
    return preprocess_text(text)


# # Apply preprocessing to the DataFrame (vectorized)
# df['processed'] = df['conversation'].apply(preprocess_text)
# df['human_processed'] = df['human_conversation'].apply(preprocess_text)
# df['assistant_processed'] = df['assistant_conversation'].apply(preprocess_text)
# df['feedback_processed'] = df['feedback_conversation'].apply(preprocess_text)

# Apply preprocessing to the DataFrame (vectorized)
df['processed'] = Parallel(n_jobs=-1)(delayed(parallel_preprocess)(text) for text in df['conversation'])
df['human_processed'] = Parallel(n_jobs=-1)(delayed(parallel_preprocess)(text) for text in df['human_conversation'])
df['assistant_processed'] = Parallel(n_jobs=-1)(delayed(parallel_preprocess)(text) for text in df['assistant_conversation'])
df['feedback_processed'] = Parallel(n_jobs=-1)(delayed(parallel_preprocess)(text) for text in df['feedback_conversation'])

# Remove empty rows
df = df[df['processed'].str.strip() != '']
df = df[df['human_processed'].str.strip() != '']
df = df.reset_index(drop=True)









# ----------------------------
# Step 3: Prepare Embeddings
# ----------------------------
docs = list(df['human_processed'])
print(f"Number of documents: {len(docs)}")
sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
#embeddings = sentence_model.encode(docs, show_progress_bar=False)
from tqdm import tqdm

docs = list(df['human_processed'])
batch_size = 1000
embeddings = []

processed_indices = []

for i in tqdm(range(0, len(docs), batch_size)):
    batch_docs = docs[i:i + batch_size]
    try:
        batch_embeddings = sentence_model.encode(batch_docs, show_progress_bar=False)
        embeddings.extend(batch_embeddings)
        processed_indices.extend(range(i, i + len(batch_docs)))
    except Exception as e:
        print(f"Error processing batch {i//batch_size}: {e}")

#missing_indices = set(range(len(docs))) - set(processed_indices)
#print(f"Missing indices: {missing_indices}")



print("Data Preprocessing Complete")



# ----------------------------
# Step 4: Apply Topic Modeling
# ----------------------------
#import time
#start_time = time.perf_counter()

current_dir = os.getcwd()
subdir="topic_models"
full_path = os.path.join(current_dir, subdir)
if not os.path.exists(full_path):
    print("topic_models subdirectory does not exist, terminating script!!")
    sys.exit(1)

loaded_model = BERTopic.load('./topic_models/', embedding_model=sentence_model)
new_model = BERTopic(language='english', nr_topics=10) #, calculate_probabilities=True, verbose=True)
topics, probs = new_model.fit_transform(df['human_processed'])
topic_model = BERTopic.merge_models([loaded_model, new_model])
topic_model.save("./topic_models/", serialization="safetensors", save_ctfidf=True, save_embedding_model=True)

def generate_topic_name(top_words):
    prompt = f"Provide a descriptive title for the topic that is described by the following stemmed and lemmatized keywords:{'. '.join(top_words)}"
    result = topic_namer(prompt)
    return result[0]['generated_text'].strip()

from transformers import pipeline
topic_namer = pipeline('text2text-generation', model='google/flan-t5-base')
topic_model.set_topic_labels( dict(zip(topic_model.get_topic_info()['Topic'] , topic_model.get_topic_info()['Representation'].apply(generate_topic_name))) )

df['Topic'] = topic_model.topics_[-len(df):]
df = pd.merge(df, topic_model.get_topic_info(), on='Topic', how='left')
df = df.rename(columns={'Representation' : 'Top_Words_BERTopic', 'CustomName' : 'Topic_Name'})

#end_time = time.perf_counter()
#elapsed_time = end_time - start_time
#print(f"Elapsed time: {elapsed_time:.4f} seconds")



print("Topic Model Fit to Data")

# ----------------------------
# Step 5: Extract and Save Document Embeddings for Visualization
# ----------------------------

reduced_embeddings = UMAP(n_neighbors=10, n_components=2, min_dist=0.0, metric='cosine').fit_transform(embeddings)
emb = pd.DataFrame(reduced_embeddings, columns=['D1', 'D2'])
df = pd.concat([df, emb], axis=1)



print("Embeddings extracted")

# ----------------------------
# Step 6: Sentiment Analysis
# ----------------------------

# def sentiment_analyzer(text):
    # sentiment = TextBlob(text)
    # score = sentiment.sentiment.polarity
    # if score > 0:
        # return "positive"
    # elif score < 0:
        # return "negative"
    # else:
        # return "neutral"

from nltk.sentiment.vader import SentimentIntensityAnalyzer
sia = SentimentIntensityAnalyzer()

def sentiment_analyzer(text):
    # Ensure the input is a string (handle NaN or None cases)
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    score = sia.polarity_scores(text)['compound']
    if score > 0:
        return "positive"
    elif score < 0:
        return "negative"
    else:
        return "neutral"

df['chat_sentiment'] = df['human_processed'].apply(sentiment_analyzer)

# BERTopic Topics
bt = topic_model.get_topic_info()[['Topic', 'Name', 'Representation']]
bt['Name'] = bt['Representation'].apply(generate_topic_name)
bt[['topword1','topword2','topword3','topword4','topword5','topword6','topword7','topword8','topword9','topword10']] = pd.DataFrame(bt.Representation.tolist(), index=bt.index)



print("Sentiment Analysis Complete")


# ----------------------------
# Step 7: Assign Topics to Documents
# ----------------------------




ct = pd.crosstab(df['Topic'], df['chat_sentiment'])
if 'negative' not in ct.columns:
  ct['negative'] = 0
if 'positive' not in ct.columns:
  ct['positive'] = 0

ct['pn_ratio'] = ct['positive'] / (ct['negative'] + ct['positive'])

bt = pd.merge(bt, ct, on="Topic")
bt.columns = [col.upper() for col in bt.columns]
bt.to_csv("./data/bertopic_topics_" + date_string + ".csv", index=False)

print("\nTopic extraction completed. Topics saved to CSV files.")





# ----------------------------
# Step 8: Extract Top Words Per Chat
# ----------------------------


# Initialize lists to store results
chat_titles = []
top_words_count = []
top_words_tfidf = []

# Parameters
no_top_words = 10  # Number of top words to extract

for index, row in df.iterrows():
    chat_title = row['title']
    processed_text = row['human_processed']
    # Ensure the input is a string (handle NaN or None cases)
    if not isinstance(processed_text, str):
        processed_text = str(processed_text) if text is not None else ""

    chat_titles.append(chat_title)

    # Split the processed text into a list of words
    tokens = processed_text.split()

    # Skip if no tokens
    if not tokens:
        top_words_count.append([])
        top_words_tfidf.append([])
        continue

    # Since we have only one document (chat), we need to reshape data accordingly
    # For CountVectorizer
    count_vectorizer = CountVectorizer()
    count_matrix = count_vectorizer.fit_transform([processed_text])
    count_array = count_matrix.toarray()[0]
    vocab = count_vectorizer.get_feature_names_out()

    # Get top words by term frequency
    word_freq = dict(zip(vocab, count_array))
    sorted_words_count = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:no_top_words]
    top_words_count.append([word for word, freq in sorted_words_count])

    # For TfidfVectorizer
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform([processed_text])
    tfidf_array = tfidf_matrix.toarray()[0]
    vocab_tfidf = tfidf_vectorizer.get_feature_names_out()

    # Get top words by TF-IDF scores
    word_tfidf = dict(zip(vocab_tfidf, tfidf_array))
    sorted_words_tfidf = sorted(word_tfidf.items(), key=lambda x: x[1], reverse=True)[:no_top_words]
    top_words_tfidf.append([word for word, score in sorted_words_tfidf])

# Add results to DataFrame
df['Top_Words_Count'] = top_words_count
df['Top_Words_TFIDF'] = top_words_tfidf





print("Top words per chat extraction complete")


# ----------------------------
# Step 8: Prepare Final DataFrame
# ----------------------------

# Prepare DataFrame for output
df_write = df[['chat_id', 'user_id', 'email', 'title', 'chat_created_at', 'chat_updated_at', 'conversation', 'num_thumbs_up', 'num_thumbs_down', 'D1', 'D2', 'chat_sentiment', 'Topic', 'Topic_Name', 'Top_Words_BERTopic', 'Top_Words_Count', 'Top_Words_TFIDF', 'model_used']]
df_write['conversation'] = df_write['conversation'].str[:50]
df_write['conversation'] = df_write['conversation'].str.replace("|", "", regex=False)
df_write.columns = [col.upper() for col in df_write.columns]
df_write.to_csv("./data/chat_log_analysis_" + date_string + ".csv", index=False, sep="|")

print("\nTopic Modeling and Sentiment Analysis completed. Results saved to CSV files.")
