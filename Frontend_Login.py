from elasticsearch import Elasticsearch
import json
import requests
import nltk
import re
import spacy
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from nltk.corpus import stopwords
import numpy as np
from warnings import simplefilter 
simplefilter(action='ignore')
import streamlit as st
stops = set(stopwords.words("english"))
import enchant
import hashlib
import sqlite3
from nltk.stem import WordNetLemmatizer
import pandas as pd
import base64
import io
from github import Github
# nltk.download("punkt")
# nltk.download("stopwords")
#nltk.download('omw-1.4')
#nltk.download('wordnet')
lm = WordNetLemmatizer()

# Github credentials
g = Github('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')

# Github repo details
owner = 'Yagneshv1'
repo_name = 'btp'
path = 'evaluation_results.csv'

# Get file contents as string
def get_file_contents(repo, file_path):
    contents = repo.get_contents(file_path)
    return base64.b64decode(contents.content).decode("utf-8")

# Update file contents on Github
def update_file_contents(repo, file_path, new_contents, commit_message):
    contents = repo.get_contents(file_path)
    repo.update_file(contents.path, commit_message, new_contents, contents.sha)


es = Elasticsearch(
    cloud_id="My_deployment:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyRkYjMwYTJjNjRmMjc0ZTdiODRkNzM1NjU1YTJmM2VkYiRiY2Y2YWFjOTBiMTg0MTBkYjIyYzNlZjRmMGMyOGI3Ng==",
    http_auth=("elastic", "bHh5kxgNzIJocCKgnPfQ7E2q")
)
# Set up the authentication credentials

username = "elastic"
password = "bHh5kxgNzIJocCKgnPfQ7E2q"

credentials = f"{username}:{password}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {encoded_credentials}",
}
max_results = 10
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
	with open('data.db', 'rb') as f:
    		file_content = f.read()
	repo = g.get_repo(f'{owner}/{repo_name}')
	update_file_contents(repo, 'data.db', file_content, "Updated user details")

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
    #st.write(word)
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

def pre_process(content):
	textwords = nltk.word_tokenize(content.lower())
	words_final = []
	for word in textwords:
		if word not in stops:
			words_final.append(lm.lemmatize(word))
			
	processed_text = ' '.join(words_final)
	return processed_text

@st.cache(allow_output_mutation=True)
def load_model():
	return spacy.load("en_core_web_lg")

def callback(count):
	#filename = "evaluation_results.csv"
	for i in range(1, count+1):
		repo = g.get_repo(f'{owner}/{repo_name}')
		df = pd.DataFrame(columns = ['Type of query', 'Query', 'Proximity Value', 'Rank', 'Score', 'Link', 'Rank', 'Feedback'])
		try:
			file_contents = get_file_contents(repo, path)
			df = pd.read_csv(io.StringIO(file_contents))
			new_row = [st.session_state.option, st.session_state.search, st.session_state.prox_value, i, st.session_state["score" + str(i)], st.session_state["link" + str(i)], st.session_state[str(i)]]
			df.loc[len(df)] = new_row
		except:
			new_row = [st.session_state.option, st.session_state.search, st.session_state.prox_value, i, st.session_state["score" + str(i)], st.session_state["link" + str(i)], st.session_state[str(i)]]
			#row = pd.Series(new_row, index=df.columns)
			#df = df.append(row, ignore_index=True)
			df.loc[len(df)] = new_row
			
		new_file_contents = df.to_csv(index=False)
		commit_message = "Update CSV file"
		update_file_contents(repo, path, new_file_contents, commit_message)
		# st.write("**Thank You! Your Feedback is submitted successfully! Please proceed for next search**")

def retrieve_required_results(output, option, query):
	#st.write(output)
	results_retrieved = output['hits']['hits']
	
	if len(results_retrieved) == 0:
		st.write('**No result Found!**')
		st.session_state.count = 1
		st.session_state["score1"] = 0
		st.session_state["link1"] = "No Result Found"
		suggestions = levenshtein_strings(query, 2)
		if len(suggestions) != 0:
			st.write("A few suggestions of the queries are as follows:")
			for i in suggestions:
				st.markdown(i)
		return
	
	count = 0
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
					try:
						matches = result['highlight']['title']
						titl = ''
						for a in matches:
							titl += a
						titl = titl.replace("<em>", "**")
						titl = titl.replace("</em>", "**")
						st.markdown(titl, unsafe_allow_html=False)
					except:
						st.write(result['_source']['title'])
					
					
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
			correct = st.radio("", ("✔️","✖️","➖"), key = str(count), index = 2)
	st.session_state.count = count

#spacy.cli.download("en_core_web_lg")

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

def callback_1():
	st.session_state.load = 1
	for i in range(1, max_results+1):
		st.session_state[str(i)] = "➖"

def main():
	if 'submitted_1' not in st.session_state:
		st.session_state['submitted_1'] = 0
	
	with st.form("my_form"):
		st.write("Please Enlcose the mandatory words to include in matches in double quotes only for **Quotes Query**")
		_ = st.text_input('Please Enter Your Search Query', key="search")

		_ = st.selectbox(
		'Choose your search method',
		('Select Query Type', 'Keyword', 'Phrase', 'Quotes', 'Image'), key='option')
		
		st.write("Use this only for Phrase queries. For other queries, let it be zero.")
		_ = st.number_input("Proximity Window Value", key="prox_value")
		
		_ = st.form_submit_button("Search", on_click = callback_1)
	

st.set_page_config(page_title="IIT PALAKKAD SEARCH PORTAL")    
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
					"stop",
					"stemmer"
				]
				},
				"search_analyzer_basic": {
					"tokenizer": "standard",
					"filter": [
						"lowercase",
						"my_synonyms",
						"stop",
						"stemmer"
					]
				},
				"search_analyzer_exact": {
				"tokenizer": "standard",
				"filter": [
					"lowercase",
					"my_synonyms"
				]
				}
			},
			"filter": {
				"my_synonyms": 
				{
					"type": "synonym_graph",
					"synonyms": ["IITPKD, IIT Palakkad, Indian Institute of technology Palakkad",
"CDC, Career Development Centre, Career Development Center",
"BAC, Board of Academic Courses",
"BOS, Board of Students",
"BoR, Board of Research",
"ESSENCE, Environmental Sciences and Sustainable Engineering Centre",
"kpal, Koninika Pal",
"CET, Centre for Education Technology",
"SAC, Student Affairs Council",
"HPC, High Performace Computing Cluster",
"CFMM, Central Facility for Materials and Manufacturing Engineering",
"CIF, Central Instrumentation Facility",
"CMFF, Central Micro-Nano Fabrication Facility",
"ICSR, IC & SR, Centre for Industry Collaboration and Sponsored Research",
"GRC, Graduate Research Council",
"CREDS, Centre for Research and Education in Data Science",
"CCI, Center for Computational Imaging",
"BoG, Board of Governors",
"IAR, International and Alumni Relations",
"MSME, Micro, Small & Medium Enterprises",
"IDC, Institute Disciplinary Committee",
"EAYL, Earn As You Learn",
"FA, Faculty Advisor",
"EWD, Engineering Works Department",
"MRBS, Room Booking System",
"IAC, Industry Academia Conclave",
"TECHIN, Technology Innovation Foundation",
"GSCOE, Global Sanitation Centre of Excellence",
"TFS, The Fleet Street",
"IPTIF, IIT Palakkad Technology IHub Foundation",
"LMS, Moodle",
"Sknayar, Sunitha K Nayar",
"svmula, Subrahmanyam Mula",
"Shk, S H Kulkarni",
"ppk, Piyush P Kurur",
"kvns, KVN Surendra",
"HVRM, HVR Mittal, Hari Vansh Rai Mittal",
"crjayan, C R Jayanarayanan",
"assekhar, A Seshadri Sekhar",
"MME, Manufacturing and Materials Engineering",
"PEPS, Power Electronics and Power Systems",
"SOCD, System on Chip Design",
"MCAM, CAM, Computing and Mathematics",
"DS, Data Science",
"CS, CSE, Computer Science and Engineering",
"EE, Electrical Engineering",
"ME, Mechanical Engineering",
"CE, Civil Engineering",
"Vadya, Music Club",
"Sync to Beat, Dance Club",
"DAC, Data Analysis Club",
"TRC, The Robotics Club",
"Shutterbug, Photography Club",
"Grafica, Arts Club",
"Akshar, Literary Arts Society, Literary Club",
"Bioscope, film-making and media club",
"YACC, Yet Another Coding Club",
"Novare, Trekking Club",
"Qriosity, Quiz Club",
"YOGSHALA, Yoga Club",
"MuSE, Museum of Science and Technology",
"Ratham, Automotive Club",
"TPO, Training and Placement Officer",
"BoB, Battle of Bands",
"SPM, Software Product Management",
"MoU, Memorandum of Understanding"
]
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


# 	requests.post(f"https://my-deployment-3de21f.es.us-central1.gcp.cloud.es.io/test_image/_close")
# 	response = requests.put(f"https://my-deployment-3de21f.es.us-central1.gcp.cloud.es.io/test1/_settings", headers= headers, data = new_settings)
# 	if response.status_code == 200:
# 		st.write("Index settings updated successfully")
# 	else:
# 		st.write(f"Error updating index settings: {response.text}")
	requests.post(f"https://my-deployment-3de21f.es.us-central1.gcp.cloud.es.io/test_image/_open")
	st.title("IIT Palakkad Search Portal")
	st.sidebar.image("iit-palakkad-logo.png")
	if "load" not in st.session_state:
		st.session_state.load = 0
	if 'search' not in st.session_state:
		st.session_state['search'] = ""
		
	menu = ["Login","SignUp"]
	choice = st.sidebar.selectbox("Menu",menu)
	
	if choice == "Login":
		username = st.sidebar.text_input("User Name", key="text_input")
		password = st.sidebar.text_input("Password", type='password')
		login = st.sidebar.checkbox("Login")
		if login:
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
				st.write("A user already exists with that name. Please choose a different name")
	if st.session_state.load and login:
		with st.form("form_2"):
			user_query = st.session_state.search
			st.session_state.load = 1
			session = requests.Session()
			uri=""
			if st.session_state.option != "Image":
				uri=f'https://my-deployment-3de21f.es.us-central1.gcp.cloud.es.io/test1/_search/?size={max_results}'
			else:
				uri=f'https://my-deployment-3de21f.es.us-central1.gcp.cloud.es.io/test_image/_search/?size={max_results}'
			json_body = ""
			flag = 0
			if st.session_state.option == "Phrase":
				flag = 1
				nlp = load_model()
				pattern = re.compile('[^\w\- ]')
				user_query = re.sub(pattern, '', user_query)
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
						"analyzer": "search_analyzer_exact",
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
				json_body = json_body.replace("prox", str(int(st.session_state.prox_value)))
			elif st.session_state.option == "Quotes":
				flag = 1
				match_phrase = re.findall(r'"(.*?)"',user_query)
				if len(match_phrase)==0:
					st.write("**No Quotes Found in Specified Query. Please enclose atleast one word in double Quotes**")
					flag = 0
					st.session_state.count = 1
					st.session_state["score1"] = 0
					st.session_state["link1"] = "No Quotes in Given Query"
					st.session_state["1"] = "➖"
				else:
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
					#st.write(json_body)
				
			elif st.session_state.option == "Keyword":
				flag = 1
				pattern = re.compile('[^\w\- ]')
				user_query = re.sub(pattern, '', user_query)
				processed_query = pre_process(user_query)
				combined_query = user_query + ' ' + processed_query
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
										{ "match": { "title": { "query" : "processed_query", "analyzer": "search_analyzer_basic", "boost": 7 }}},
										{"match": {"processed_text":  {"query" : "processed_query", "analyzer": "search_analyzer_basic", "boost": 5}}},
										{"match": {"text":  {"query" : "combined_query", "analyzer" : "search_analyzer_basic", "boost": 0}}},
										{ "match": { "title": { "query" : "processed_query",  "analyzer": "search_analyzer", "boost":3}}},
										{"match": {"processed_text":  {"query" : "user_query", "analyzer": "search_analyzer", "boost":2}}},
										{"match": {"text":  {"query" : "user_query", "analyzer": "search_analyzer", "boost": 0}}},
										{ "match": { "processed_text": { "query" : "processed_query", "fuzziness" : "AUTO", "analyzer": "search_analyzer"}}},
										{ "match": { "text": { "query" : "combined_query", "fuzziness" : "AUTO", "analyzer": "search_analyzer", "boost" : 0}}}
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
				json_body = json_body.replace("processed_query", processed_query)
				json_body = json_body.replace("combined_query", combined_query)
			elif st.session_state.option == "Image":
				flag = 1
				processed_tokens = []
				for i in nltk.word_tokenize(user_query):
					if i not in stops:
						processed_tokens.append(i)

				user_query = ' '.join(processed_tokens)
				pattern = re.compile('[^\w\- ]')
				user_query = re.sub(pattern, '', user_query)
				st.write(user_query)
				json_body = """{
								"query":
										{
											"bool":
											{
												"should":[
														{"match": {"title": {"boost" : 5, "query" : "user_query", "analyzer": "search_analyzer_basic"}}},
														{"match": {"section": {"boost" : 6, "query" : "user_query", "analyzer": "search_analyzer_basic"}}},
														{"match": {"processed_desc":{"boost" : 4, "query" : "user_query", "analyzer": "search_analyzer_basic"}}},
														{"match": {"title": {"boost" : 2, "query" : "user_query", "analyzer": "search_analyzer"}}},
														{"match": {"section": {"boost" : 3, "query" : "user_query", "analyzer": "search_analyzer"}}},
														{"match": {"processed_desc": {"boost" : 1, "query" : "user_query", "analyzer": "search_analyzer"}}}
														],
												"minimum_should_match" : 1
											}
										}
								}
				"""
				json_body = json_body.replace("user_query", user_query)
				#st.write(json_body)
			if flag:
				fetch(session, uri, headers, json_body, st.session_state.option, user_query)
				submitted = st.form_submit_button("Submit Feedback", on_click = callback, args = [st.session_state.count])
			else:
				_ = st.form_submit_button("Start Searching")
