from elasticsearch import Elasticsearch
import json
import requests
import nltk
import spacy
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import wordnet
from nltk.corpus import stopwords
import numpy as np
from warnings import simplefilter 
simplefilter(action='ignore', category=DeprecationWarning)
import streamlit as st

stops = set(stopwords.words("english"))
st.set_page_config(page_title="IIT PALAKKAD SEARCH PORTAL")
st.write("Welcome to IIT Palakkad Search Portal")
st.sidebar.image("iit-palakkad-logo.png") 

def retrieve_required_results(output, query):
	print(output)
	results = output['hits']['hits']
	
	if len(results) == 0:
		st.write('No result Found!')
		return 

	for result in results:
		st.write('Document Score:', result['_score'])
		st.write('Page Link:', result['_source']['page_link'])
		st.write('Image URL:', result['_source']['image_link'])
		#snippet = ''
		#try:
			#matches = result['highlight']['image_desc']
			#for a in matches:
			#	snippet += a + '...'
			#snippet = snippet.replace("<em>", "**")
			#snippet = snippet.replace("</em>", "**")
			#st.write('Page Title:', result['_source']['page_title'])
			
		#except:
			#matches = result['highlight']['title']
			#titl = ''
			#for a in matches:
				#titl += a
			#titl = titl.replace("<em>", "**")
			#titl = titl.replace("</em>", "**")
			#st.markdown(titl, unsafe_allow_html=False)

			#snippet = result['_source']['image_desc'][:250] + '...'
		#st.markdown(snippet, unsafe_allow_html=False)
		st.write('\n\n')
#spacy.cli.download("en_core_web_lg")
#nlp = spacy.load("en_core_web_lg")

with st.form("form"):
	uri='http://localhost:9200/test/_search/?size=20'
	headers = {'Content-Type' : 'application/json',}
	user_query = st.text_input('Please Enter Your Keywords', key="search")
	option = st.selectbox(
    'Choose your search method',
    ('Keyword', 'Phrase', 'Image'))
	submitted = st.form_submit_button("Search")

	match_query = '''{"match_phrase":{"text": {"query" : query_part,"slop" : 20}}}'''
	if submitted:
		tokens = []
		for token in nltk.word_tokenize(user_query):
			if token not in stops:
				tokens.append(token)
		user_query = " ".join(tokens)
		#doc = nlp(user_query)
		#ners = [str(i) for i in doc.ents]
		#tokens = []
		#for ent in ners:
			#for token in nltk.word_tokenize(ent):
				#tokens.append(token)
		#for i in user_query.split():
			#if i not in tokens and i not in stops:
				#ners.append(i.lower())
		#final_query_words = []
		#for i in ners:
			#final_query_words.append(match_query.replace("query_part", "\"" + i + "\""))
		#final_query = ','.join(final_query_words)		
        
		json_body = ""
		if option == "Phrase":
			json_body = '''
				{
					"query" : 
					{
						"bool": 
						{
							"should": 
							[
								match_part
							]
						}
					},
					"highlight": {
					    "fields" : {
						"text" : {}, "title" : {}
					    }
					  }
				}
				'''
			json_body = json_body.replace("match_part", final_query)
		else:
			#user_query = ' '.join(ners)
			
			json_body = """{
				"query":{
					"bool":{
						"should":[ 
						{"match": {"processed_desc":{"boost" : 1, "query" :\"""" + user_query + """\"}}}],
						"minimum_should_match" : 1
						}
					},
					"highlight": {
					    "fields" : {
						"image_desc" : {}
					    }
					  }
				}
			"""

			st.write(json_body)

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

