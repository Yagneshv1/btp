from elasticsearch import Elasticsearch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
import json
import requests
import nltk
import spacy
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import wordnet
from nltk.corpus import stopwords
import re
import numpy as np
from warnings import simplefilter 
simplefilter(action='ignore', category=DeprecationWarning)
import streamlit as st

stops = set(stopwords.words("english"))
st.set_page_config(page_title="IIT PALAKKAD SEARCH PORTAL")
st.write("Welcome to IIT Palakkad Search Portal")
st.sidebar.image("iit-palakkad-logo.png") 

def compute_scores(word_scores, sentence):
	result = 0.0
	for m in word_tokenize(sentence):
		result += word_scores.get(m.lower(), 0)

	return result


def generate_snippets(results, query):
	if len(results) == 0:
		return
	query = query.lower()
	snippets = {}
	documents= []
	for result in results:
		documents.append(result['_source']['text'])
	
	tfidf = TfidfVectorizer()
	tfidf.fit_transform(documents)
	tfidfs = {}
	for ele1, ele2 in zip(tfidf.get_feature_names(), tfidf.idf_):
		tfidfs[ele1] = ele2
	
	vectorizer = CountVectorizer()
	X = vectorizer.fit_transform(documents)
	vocab = tfidf.vocabulary_
	X = X.toarray()

	query_tokens = word_tokenize(query)
	#Now the actual snippet generation starts.
	for i in range(len(results)):
		document = results[i]['_source']['text']
		tokens = word_tokenize(document)
		word_scores = {}
		#st.write(tokens)
		for j in range(len(tokens)):
			if tokens[j].lower() in query_tokens:
				word_scores[tokens[j].lower()] = tfidfs.get(tokens[j].lower()) * X[i][vocab[tokens[j].lower()]]

		
		for token in tokens:
			if token in query_tokens:
				word_scores[token] = tfidfs.get(token, 0)
		
		res = []
		for sent in sent_tokenize(document):
			res.append((sent, compute_scores(word_scores, sent)))

		res.sort(key = lambda x: x[1], reverse = True)
		#st.write(res)
		snippet = ''

		count = 0
		for k in res:
			if k[1] > 0.0 and count < 1:
				snippet += '...' + k[0]
				count +=1
		
		for t in user_query.split():
			snippet = re.sub(r"\b%s\b" %t, r"**\g<0>**", snippet, flags=re.IGNORECASE)
			

		snippets[results[i]['_id']] = snippet
	return snippets

def retrieve_required_results(output, query):
	print(output)
	results = output['hits']['hits']
	#Results may be merged based on the id of the document
	#text_snippets = generate_snippets(results, query)
	
	if len(results) == 0:
		st.write('No result Found!')
		return 

	for result in results:
		st.write('Document Score:', result['_score'])
		st.write('Page Link:', result['_source']['page_link'])
		#st.write('Page Title:', result['_source']['title'])
		
		'''snippet = ''
		try:
			matches = result['highlight']['text']
			for a in matches:
				snippet += a + '...'
			snippet = snippet.replace("<em>", "**")
			snippet = snippet.replace("</em>", "**")
			st.write('Page Title:', result['_source']['title'])
		#st.markdown(text_snippets[result['_id']], unsafe_allow_html=False)
			
		except:
			matches = result['highlight']['title']
			titl = ''
			for a in matches:
				titl += a
			titl = titl.replace("<em>", "**")
			titl = titl.replace("</em>", "**")
			st.markdown(titl, unsafe_allow_html=False)

			snippet = result['_source']['text'][:250] + '...'
		st.markdown(snippet, unsafe_allow_html=False)'''
		st.write('\n\n')
	
nlp = spacy.load("en_core_web_lg")

with st.form("form"):
	uri='http://localhost:9200/test/_search/?size=20'
	headers = {'Content-Type' : 'application/json',}
	user_query = st.text_input('Please Enter Your Keywords', key="search")
	submitted = st.form_submit_button("Search")
	textwords = nltk.word_tokenize(user_query.lower())
	# textwords = [word for word in textwords if word.isalnum()]
	# words_final = []
	'''for word in textwords:
		if word not in stops:
			words_final.append(word)
	user_query = ' '.join(words_final)'''
	final_query = ''
	if submitted:
		doc = nlp(user_query)
		ners = doc.ents
		print(ners)
		tokens = []
		if len(ners)!=0:
			entity_query = str(ners[0])
			for i in range(1,len(ners)):
				entity_query = entity_query + ' OR ' + str(ners[i])
			for ent in ners:
				for token in nltk.word_tokenize(str(ent)):
					tokens.append(token)
			for i in query.split():
				if i not in tokens:
					entity_query = entity_query + ' OR ' + i
			print(entity_query)
			for i in entity_query.split():
				if i=='OR':
					final_query = final_query + i
				elif i not in stops:
					final_query = final_query + i.lower()
			print(final_query)
		json_body = """
			{
				"query":
				{
					"query_string": {
						"query": "(Senate) OR (Member)",
      					"default_field": "text"
					}
				}
			}

			"""
		#print(json_body)
		try:
			resp = requests.get(uri, headers=headers, data=json_body)
			try:
				resp_text = json.loads(resp.text)
			except:
				resp_text = resp.text
		
		except Exception as error:
			st.write(error)
			resp_text = error
		
		retrieve_required_results(resp_text, user_query)
