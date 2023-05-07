from elasticsearch import Elasticsearch
import json
import requests
import nltk
nltk.download("punkt")
nltk.download("stopwords")
import re
import spacy
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from nltk.corpus import stopwords
import numpy as np
from warnings import simplefilter 
simplefilter(action='ignore', category=DeprecationWarning)
import streamlit as st
from csv import writer
stops = set(stopwords.words("english"))
import enchant
import hashlib
import sqlite3 
es = Elasticsearch(
    cloud_id="My_deployment:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyRkYjMwYTJjNjRmMjc0ZTdiODRkNzM1NjU1YTJmM2VkYiRiY2Y2YWFjOTBiMTg0MTBkYjIyYzNlZjRmMGMyOGI3Ng==",
    http_auth=("elastic", "bHh5kxgNzIJocCKgnPfQ7E2q")
)

def make_hashes(password):
	return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password,hashed_text):
	if make_hashes(password) == hashed_text:
		return hashed_text
	return False

conn = sqlite3.connect('data.db')
c = conn.cursor()
def create_usertable():
	c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT PRIMARY KEY,password TEXT)')


def add_userdata(username,password):

	c.execute('INSERT INTO userstable(username,password) VALUES (?,?)',(username,password))
	conn.commit()

def login_user(username,password):
	c.execute('SELECT * FROM userstable WHERE username =? AND password = ?',(username,password))
	data = c.fetchall()
	return data


def levenshtein_distance(s1, s2):
    # Initialize a matrix of size (len(s1) + 1) x (len(s2) + 1) with 0s
    matrix = [[0 for j in range(len(s2) + 1)] for i in range(len(s1) + 1)]
    
    # Fill in the first row and column with the indices
    for i in range(len(s1) + 1):
        matrix[i][0] = i
    for j in range(len(s2) + 1):
        matrix[0][j] = j
    
    # Fill in the rest of the matrix with the Levenshtein distances
    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            if s1[i-1] == s2[j-1]:
                matrix[i][j] = matrix[i-1][j-1]
            else:
                matrix[i][j] = 1 + min(matrix[i-1][j], matrix[i][j-1], matrix[i-1][j-1])
    
    # Return the Levenshtein distance between the two strings
    return matrix[len(s1)][len(s2)]
    
def levenshtein_strings(word, distance):
    # Generate all strings within the given Levenshtein distance from the word
    result = set()
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    d = enchant.Dict("en_US")
    for i in range(len(word)):
        for c in alphabet:
            new_word = word[:i] + c + word[i:]
            if levenshtein_distance(new_word, word) <= distance and d.check(new_word):
                result.add(new_word)
        if i < len(word) - 1:
            new_word = word[:i] + word[i+1] + word[i] + word[i+2:]
            if levenshtein_distance(new_word, word) <= distance and d.check(new_word):
                result.add(new_word)
    for i in range(len(word)):
        for c in alphabet:
            new_word = word[:i] + c + word[i+1:]
            if levenshtein_distance(new_word, word) <= distance and d.check(new_word):
                result.add(new_word)
    return result

@st.cache(allow_output_mutation=True)
def load_model():
	return spacy.load("en_core_web_lg")

def callback(count):
	filename = "evaluation_results.csv"
	for i in range(1, count+1):
		with open(filename, 'a') as f_object:
	
			writer_object = writer(f_object)

			# writer_object.writerow([st.session_state.search, st.session_state["link" + str(i)],st.session_state["score" + str(i)], st.session_state.option, st.session_state[str(i)]])
			writer_object.writerow([st.session_state.option, st.session_state.search, st.session_state.prox_value, st.session_state["score" + str(i)], st.session_state["link" + str(i)], st.session_state[str(i)]])

			f_object.close()

def retrieve_required_results(output, option, query):
	print(output)
	results_retrieved = output['hits']['hits']
	
	if len(results_retrieved) == 0:
		st.write('**No result Found!**')
		
		suggestions = levenshtein_strings(query, 2)
		if len(suggestions) != 0:
			st.write("A few suggestions of the queries are as follows:")
			for i in suggestions:
				st.markdown(i)
		return
	
	count = 0
	with st.form("form_1"):
		for result in results_retrieved:
			count += 1
			col1, col2 = st.columns([4,1])
			with col1:
				st.write('Document Score:', result['_score'])
				st.write('Page Link:', result['_source']['page_link'])
				st.session_state['link' + str(count)] = result['_source']['page_link']
				st.session_state['score' + str(count)] = result['_score']
				if option != "Image":
					snippet = ''
					try:
						matches = result['highlight']['text']
						for a in matches:
							snippet += a + '...'
						snippet = snippet.replace("<em>", "**")
						snippet = snippet.replace("</em>", "**")

						st.write('Page Title:', result['_source']['title'])
						
					except:
						matches = result['highlight']['title']
						titl = ''
						for a in matches:
							titl += a
						titl = titl.replace("<em>", "**")
						titl = titl.replace("</em>", "**")
						st.markdown(titl, unsafe_allow_html=False)

						snippet = result['_source']['text'][:250] + '...'
					st.markdown(snippet, unsafe_allow_html=False)
				else:
					url = result['_source']['image_link']
					st.session_state['link' + str(count)] = result['_source']['image_link']
					if not url.startswith("https://"):
						url = "https://" + url

					st.image(url)
					st.write('Image URL:', result['_source']['image_link'])
				
				st.write('\n\n')
			with col2:
				correct = st.radio("", ("✔️","✖️"), key = str(count), index = 1)
		submitted_1 = st.form_submit_button("Submit Feedback", on_click=callback, args = [count])

# spacy.cli.download("en_core_web_lg")

def fetch(session, url, headers, json_body, option, query):
	try:
		resp = session.get(url, headers=headers, data=json_body)
		
		try:
			resp_text = json.loads(resp.text)
		except:
			resp_text = resp.text
		
	except Exception as error:
		st.write(error)
		resp_text = error
		print(resp_text)	
	retrieve_required_results(resp_text, option, query)


def results(user_query, option, proximity_value=0):
	print('Query is', user_query)
	session = requests.Session()
	uri=""
	if option != "Image":
		uri='http://localhost:9200/test2/_search/?size=20'
	else:
		uri='http://localhost:9200/test_image/_search/?size=20'
	headers = {'Content-Type' : 'application/json',}
	json_body = ""
	if option == "Phrase":
		nlp = load_model()
		doc = nlp(user_query)
		ners = [str(i) for i in doc.ents]
		
		tokens = []
		for ent in ners:
			for token in nltk.word_tokenize(ent):
				tokens.append(token)

		for i in user_query.split():
			if i not in tokens and i not in stops:
				ners.append(i.lower())

		final_query_words = []
		for i in ners:
			final_query_words.append(''' \\"''' + i + '''\\" ''')

		final_query = ' '.join(final_query_words)		
		print(final_query)

		json_body = '''
		{	"query": 
			{
				"multi_match" : {
				"query":      "match_part",
				"type":       "phrase",
				"fields":     [ "title^4", "text" ],
				"analyzer": "search_analyzer",
				"slop" : "prox"
				}
			},
			"highlight": 
			{
				"fields" : 
				{
					"text" : {}, "title" : {}
				}
			}
		}'''
		
		
		
		json_body = json_body.replace("match_part", final_query)
		json_body = json_body.replace("prox", str(int(proximity_value)))
		print(json_body)
	elif option == "Quotes":
		match_phrase = re.findall(r'"(.*?)"',user_query)
		print(match_phrase)
		if len(match_phrase)==0:
			raise Exception("No Quotes Found in Specified Query")
		
		user_query = re.sub(r'"(.*?)"', "", user_query)
		non_quote_terms = []
		for i in user_query.split():
			if i not in stops:
				non_quote_terms.append(i)

		boolean_query = ""
		for i in match_phrase:
			if len(boolean_query) == 0:
				boolean_query = "(" + ' AND '.join(["(" + j + ")" for j in i.split()]) + ")"
			else:
				boolean_query = boolean_query + " AND " +  "(" + ' AND '.join(["(" + j + ")" for j in i.split()]) + ")"
		if len(boolean_query) != 0:
			boolean_query = "(" + boolean_query + ")"

		#Default fuzziness is 2 sufficient to catch 80% of spelling mistakes
		for i in non_quote_terms:
			boolean_query = boolean_query + " OR " + "(" + i + "~)"

		print(boolean_query)
		json_body = '''
			{
				"query" : 
				{
					"query_string": {
						"query": "match_part",
						"fields" : ["title^2", "text"]
					}
				},
				"highlight": {
					"fields" : {
					"text" : {}, "title" : {}
					}
				}
			}
			'''
		json_body = json_body.replace("match_part", boolean_query)
		print(json_body)
	
	elif option == "Keyword":
		
		# json_body = '''{
		# 				"query":
		# 						{
		# 							"bool":
		# 							{
		# 								"should":[
		# 										{"match": {"title": {"boost" : 2, "query" : "user_query",  "analyzer": "search_analyzer"}}}, 
		# 										{"match": {"text":  {"boost" : 1, "query" : "user_query", "fuzziness" : "AUTO", "analyzer": "search_analyzer"}}}
		# 										],
		# 								"minimum_should_match" : 1
		# 							}
		# 						},
		# 				"highlight": 
		# 						{
		# 						"fields" : 
		# 								{
		# 									"text" : {}, "title" : {}
		# 								}
		# 						}
		# 				}
		# '''\
		json_body = '''
        {
            "query": 
			{
                "function_score": 
				{
					"query": 
					{
						"bool": 
					
						{
							"should": 
							[
								{ "match": { "title": { "query" : "user_query",  "analyzer": "search_analyzer", "boost": 10 }}},
								{"match": {"text":  {"query" : "user_query", "analyzer": "search_analyzer", "boost":5}}},
								{ "match": { "text": { "query" : "user_query", "fuzziness" : "AUTO", "analyzer": "search_analyzer"}}}
							]
						}
					},
					"score_mode": "sum",
					"boost_mode": "sum"
                }
            }
            	,
					"highlight": 
						{
							"fields" : 
							{
								"text" : {}, "title" : {}
							}
						}		
	    }
        '''

		json_body = json_body.replace("user_query", user_query)
	
	elif option == "Image":
		processed_tokens = []
		for i in nltk.word_tokenize(user_query):
			if i not in stops:
				processed_tokens.append(i)

		user_query = ' '.join(processed_tokens)
		
		json_body = """{
						"query":
								{
									"bool":
									{
										"should":[
												{"match": {"title": {"boost" : 2, "query" : "user_query", "analyzer": "search_analyzer"}}},
												{"match": {"section": {"boost" : 4, "query" : "user_query", "analyzer": "search_analyzer"}}},
												{"match": {"processed_desc":{"boost" : 1, "query" : "user_query", "analyzer": "search_analyzer"}}}
												],
										"minimum_should_match" : 1
									}
								}
						}
		"""
		json_body = json_body.replace("user_query", user_query)
		#st.write(json_body)

	fetch(session, uri, headers, json_body, option, user_query)

def temp():
	if st.session_state.option == 'Phrase':
		results(st.session_state.search, st.session_state.option, st.session_state.prox_value)
	else:
		results(st.session_state.search, st.session_state.option)

def main():
	if 'submitted_1' not in st.session_state:
		st.session_state['submitted_1'] = 0

	with st.form("form"):
		_ = st.text_input('Please Enter Your Search Query', key="search")

		_ = st.selectbox(
		'Choose your search method',
		('Keyword', 'Phrase', 'Quotes', 'Image'), key='option')

		_ = st.number_input("Enter the value for Proximity Search", key="prox_value")
		
		st.form_submit_button("Search", on_click=temp)
    
if __name__ == "__main__":
	new_settings = json.dumps({
		"settings": {
			"analysis": {
			"analyzer": {
				"search_analyzer": {
				"tokenizer": "standard",
				"filter": [
					"lowercase",
					"my_synonyms",
					"all_synonyms",
					"stop"
				]
				}
			},
			"filter": {
				"my_synonyms": 
				{
					"type": "synonym_graph",
					"synonyms_path": "synonyms.txt"
				},
				"all_synonyms":{
					"type" : "synonym_graph",
					"format" : "wordnet",
					"synonyms": [
					"s(100000001,1,'abstain',v,1,0).",
					"s(100000001,2,'refrain',v,1,0).",
					"s(100000001,3,'desist',v,1,0)."
					]
				}
			}
			}
		}
		})
	
	headers = {'Content-Type' : 'application/json',}
	requests.post(f"http://localhost:9200/test2/_close")
	response = requests.put(f"http://localhost:9200/test2/_settings", headers= headers, data = new_settings)
	requests.post(f"http://localhost:9200/test2/_open")

	requests.post(f"http://localhost:9200/test_image/_close")
	response = requests.put(f"http://localhost:9200/test_image/_settings", headers= headers, data = new_settings)
	requests.post(f"http://localhost:9200/test_image/_open")

	if response.status_code == 200:
		print("Index settings updated successfully")
	else:
		print(f"Error updating index settings: {response.text}")

	st.set_page_config(page_title="IIT PALAKKAD SEARCH PORTAL")
	st.title("IIT Palakkad Search Portal")
	st.sidebar.image("iit-palakkad-logo.png")
	
	menu = ["Login","SignUp"]
	choice = st.sidebar.selectbox("Menu",menu)
	
	if choice == "Login":
		username = st.sidebar.text_input("User Name", key="text_input")
		password = st.sidebar.text_input("Password", type='password')

		if st.sidebar.checkbox("Login"):
			create_usertable()
			hashed_pswd = make_hashes(password)
			result = login_user(username,check_hashes(password,hashed_pswd))
			if result:
				st.success("Logged In as {}".format(username))
				main()
				password = ""
			else:
				st.warning("Incorrect Username/Password")

	elif choice == "SignUp":
		st.subheader("Create New Account")
		new_user = st.text_input("Username")
		new_password = st.text_input("New Password",type='password', value = '')

		if st.button("Signup"):
			create_usertable()
			try:
				add_userdata(new_user,make_hashes(new_password))
				st.success("You have successfully created a valid Account")
				st.info("Go to Login Menu to login")
			except Exception as e:
				st.write("A user already exists with the name. Please choose a different name")
