#Code implementation of Test Version of Search Options

#Importing the required libraries
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

# Github credentials to access repository to collect the evaluation results. Can be removed in production version. Replace with own credentials
g = Github('XXXXXXXXXXXXX')	#Access token

# Github repo details
owner = 'Yagneshv1'	#Name of the owner
repo_name = 'btp'	#Repository name to store
path = 'evaluation_results.csv'	#File name

# Get file contents as string
def get_file_contents(repo, file_path):
    contents = repo.get_contents(file_path)
    return base64.b64decode(contents.content).decode("utf-8")

# Update file contents on Github
def update_file_contents(repo, file_path, new_contents, commit_message):
    contents = repo.get_contents(file_path)
    repo.update_file(contents.path, commit_message, new_contents, contents.sha)

#Elastic Cloud credentials to access the indexed data. Replace with own details
es = Elasticsearch(
    cloud_id="XXXXXXX",
    http_auth=("XXX", "XXXX")	#Username and password to be entered
)

# Set up the authentication credentials. #Username and password to be entered
username = "XX"
password = "XXX"

credentials = f"{username}:{password}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {encoded_credentials}",
}

max_results = 10	#Number of results to display on search

#Encrypt the user login details using hashing
def make_hashes(password):
	return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password,hashed_text):
	if make_hashes(password) == hashed_text:
		return hashed_text
	return False

conn = sqlite3.connect('data.db')
c = conn.cursor()
def create_usertable():
	'''
 	Creates a table for new user to the portal.
 	'''
	c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT PRIMARY KEY,password TEXT)')

def add_userdata(username,password):
	'''
 	Add the credentials of the user to the database
 	'''
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
    '''
    Computes the levenshtein distance between words.
    '''
    matrix = [[0 for j in range(len(s2) + 1)] for i in range(len(s1) + 1)]
    
    for i in range(len(s1) + 1):
        matrix[i][0] = i
    for j in range(len(s2) + 1):
        matrix[0][j] = j

    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            if s1[i-1] == s2[j-1]:
                matrix[i][j] = matrix[i-1][j-1]
            else:
                matrix[i][j] = 1 + min(matrix[i-1][j], matrix[i][j-1], matrix[i-1][j-1])

    return matrix[len(s1)][len(s2)]
    
def levenshtein_strings(word, distance):
    '''
    Generates possible meaningful english words within the maximum distance provided
    '''
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
	'''
 	Function to pre-process the text. Involves lowercasing, stop word removal and lemmatization.
 	'''
	textwords = nltk.word_tokenize(content.lower())
	words_final = []
	for word in textwords:
		if word not in stops:
			words_final.append(lm.lemmatize(word))
			
	processed_text = ' '.join(words_final)
	return processed_text

#Caching spacy model to avoid loading in every run of the Streamlit code.
@st.cache(allow_output_mutation=True)
def load_model():
	return spacy.load("en_core_web_lg")

#Uncomment and run the next line for the first time execution of the code.
#spacy.cli.download("en_core_web_lg")

def callback(count):
	'''
 	Store the feedback provided by the user directly in the GitHub file.
  	'''

	for i in range(1, count+1):
		repo = g.get_repo(f'{owner}/{repo_name}')
		df = pd.DataFrame(columns = ['Type of query', 'Query', 'Proximity Value', 'Rank', 'Score', 'Link', 'Feedback'])
		try:
			file_contents = get_file_contents(repo, path)
			df = pd.read_csv(io.StringIO(file_contents))
			new_row = [st.session_state.option, st.session_state.search, st.session_state.prox_value, i, st.session_state["score" + str(i)], st.session_state["link" + str(i)], st.session_state[str(i)]]
			df.loc[len(df)] = new_row
		except:
			new_row = [st.session_state.option, st.session_state.search, st.session_state.prox_value, i, st.session_state["score" + str(i)], st.session_state["link" + str(i)], st.session_state[str(i)]]
			df.loc[len(df)] = new_row
			
		new_file_contents = df.to_csv(index=False)
		commit_message = "Update CSV file"
		update_file_contents(repo, path, new_file_contents, commit_message)
	st.write("**Thank You! Your Feedback is submitted successfully! Please proceed for next search**")

def retrieve_required_results(output, option, query):
	#Extract the hits from all the matches obtained
	results_retrieved = output['hits']['hits']

	#When there are no results found, for single word queries, we provide some suggestions based on maximum levenstein distance of 2.
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

	#For all other cases, the following details are displayed against each result
	count = 0
	for result in results_retrieved:
		count += 1
		col1, col2 = st.columns([4,1])
		with col1:
			st.write('Document Score:', result['_score'])	#Score of the document
			st.write('Page Link:', result['_source']['page_link'])	#Page link
			st.session_state['link' + str(count)] = result['_source']['page_link']
			st.session_state['score' + str(count)] = result['_score']
			if option != "Image":	#For non-image type search, snippets are displayed.
				snippet = ''
				try:
					#Try to get matches in text field first and then try for title(if possible).
					matches = result['highlight']['text']	#Extract the matches from highlight section.
					#Convert the matching terms to bold for displaying and combine various matches by ...
					#Highlighting is done both in title and text fields.
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
					#In case there are not matches in text try it on title field. In this case, the text snippet is considered the first 250 characters of the document text.
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
				#In case of images, we render the image instead of the snippet.
				url = result['_source']['image_link']
				st.session_state['link' + str(count)] = result['_source']['image_link']
				if not url.startswith("https://"):
					url = "https://" + url

				st.image(url)
				st.write('Image URL:', result['_source']['image_link'])
			
			st.write('\n\n')
			
		#Radio buttons are provided to the user for submitting feedback.
		with col2:
			correct = st.radio("", ("✔️","✖️","➖"), key = str(count), index = 2)
	st.session_state.count = count


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
	#The default feedback is set to not responded for all the results.
	for i in range(1, max_results+1):
		st.session_state[str(i)] = "➖"

def main():
	if 'submitted_1' not in st.session_state:
		st.session_state['submitted_1'] = 0

	#Front-end options to the user.
	#Search box to enter the query. Dropdown to choose the kind of query and enter the Proximity value(phrase query)
	with st.form("my_form"):
		st.write("Please Enlcose the mandatory words to include in matches in double quotes only for **Quotes Query**")
		_ = st.text_input('Please Enter Your Search Query', key="search")

		_ = st.selectbox(
		'Choose your search method',
		('Select Query Type', 'Keyword', 'Phrase', 'Quotes', 'Image'), key='option')
		
		st.write("Use this only for Phrase queries. For other queries, let it be zero.")
		_ = st.number_input("Proximity Window Value", key="prox_value")
		
		_ = st.form_submit_button("Search", on_click = callback_1)
		#Once the user submits, function(callback_1) is called in the backend.
		st.write("**Please submit the feedback of the results through submit feedback button after the search results!!**")
	

st.set_page_config(page_title="IIT PALAKKAD SEARCH PORTAL")    
if __name__ == "__main__":
	#Creating custom analysers with various filters used during the search.
	# lowercase filter - lower cases. my_synonyms - Custom synonyms provided. all_synonyms - Global synonyms list, stop - Stopwords remover, stemmer - Apply stemming
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
#You may add all the synonyms that you feel relevant in the all_synonyms filter above or in my_synonyms. Please use my_synonyms for institute-specific terms preferably. These lists can also be given in a file and the link may be provided to the filter. Refer to ELastic Search documentation for more details.

#Uncomment the below lines on the indices deployed on cloud to incorporate the settings. Do not forget to rename the index to the name in your code.
#In order to apply the setting, first close the index apply and reopen it.
	
# 	requests.post(f"https://my-deployment-3de21f.es.us-central1.gcp.cloud.es.io/test_image/_close")
# 	response = requests.put(f"https://my-deployment-3de21f.es.us-central1.gcp.cloud.es.io/test1/_settings", headers= headers, data = new_settings)
# 	if response.status_code == 200:
# 		st.write("Index settings updated successfully")
# 	else:
# 		st.write(f"Error updating index settings: {response.text}")
#	requests.post(f"https://my-deployment-3de21f.es.us-central1.gcp.cloud.es.io/test_image/_open")
	st.title("IIT Palakkad Search Portal")
	st.sidebar.image("iit-palakkad-logo.png")
	if "load" not in st.session_state:
		st.session_state.load = 0
	if 'search' not in st.session_state:
		st.session_state['search'] = ""

	#Main-menu for the user.
	menu = ["Login","SignUp"]
	choice = st.sidebar.selectbox("Menu",menu)
	
	if choice == "Login":
		username = st.sidebar.text_input("User Name", key="text_input")
		password = st.sidebar.text_input("Password", type='password')
		login = st.sidebar.checkbox("Login")
		#When the user chooses login option all his details gets verified in the backend and will be redirected to portal upon successful login.
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
			#Post the requests to respective index depending on the type of query.
			if st.session_state.option != "Image":
				uri=f'https://my-deployment-3de21f.es.us-central1.gcp.cloud.es.io/test1/_search/?size={max_results}'
			else:
				uri=f'https://my-deployment-3de21f.es.us-central1.gcp.cloud.es.io/test_image/_search/?size={max_results}'
			json_body = ""
			flag = 0
			if st.session_state.option == "Phrase":
				#For the phrase query, identify the named entities using spacy.encore_web_lg model.
				flag = 1
				nlp = load_model()
				pattern = re.compile('[^\w\- ]')
				user_query = re.sub(pattern, '', user_query)
				doc = nlp(user_query)
				ners = [str(i) for i in doc.ents]
				
				tokens = []
				#Get all the tokens part of the named entities
				for ent in ners:
					for token in nltk.word_tokenize(ent):
						tokens.append(token)
						
				#Append the remaining tokens also to the list
				for i in user_query.split():
					if i not in tokens and i not in stops:
						ners.append(i.lower())

				final_query_words = []
				for i in ners:
					final_query_words.append(''' \\"''' + i + '''\\" ''')

				final_query = ' '.join(final_query_words)		
				print(final_query)
				
				#Final query has the terms in entities within quotes as a unit and for convenience, even the non-entities are enclosed in quotes as a single term.
				#The query description is as follows:
				'''
    				We consider phrase type of multimatch query with 4x boost on the title than text field.
				proximity window value is determined by the slop.
    				Only the lowercasing and synonyms are considered during the match.
				Search is performed on the original text since the phrase expects all the exact terms in the matches.
    				'''
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
				#For quote queries, we first check if the query has quotes. If not exception is given to the user.
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
					
					#Extract all the terms which are not in quotes which are non-mandatory terms in the document for matching.
					non_quote_terms = []
					for i in user_query.split():
						if i not in stops:
							non_quote_terms.append(i)

					boolean_query = ""
					#Join all the words within the quotes with AND operator. Each unit of quote terms are enclosed in () denoting an entity"
					for i in match_phrase:
						if len(boolean_query) == 0:
							boolean_query = "(" + ' AND '.join(["(" + j + ")" for j in i.split()]) + ")"
						else:
							boolean_query = boolean_query + " AND " +  "(" + ' AND '.join(["(" + j + ")" for j in i.split()]) + ")"
					if len(boolean_query) != 0:
						boolean_query = "(" + boolean_query + ")"

					#Default fuzziness is 1 sufficient to catch 80% of spelling mistakes. Only for Non-Quote terms
					for i in non_quote_terms:
						boolean_query = boolean_query + " OR " + "(" + i + "~)"

					print(boolean_query)
					#Match the query on the indexed documents with query_string type with boost for title. No filters are used since it expects an exact match.
					#Search is performed on the original text itself.
					
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
				#For keyword queries, we create a new query with both original and pre-processed query(Query-Expansion). It is only to create the highlighting in snippets
				
				flag = 1
				pattern = re.compile('[^\w\- ]')
				user_query = re.sub(pattern, '', user_query)
				processed_query = pre_process(user_query)
				combined_query = user_query + ' ' + processed_query

				'''
    				The scoring is as follows:
				-Title is matched on the processed query with highest weightage(stemming, stopwords removed, synonyms)
    				-Match is performed on the processed text content with next highest boosting.
				-Zero boost is given for text field matches. This is just for highlighting purposes in the snippets.
    				-Synonyms considered cases are given next highest weightages.
				-Then, finally fuzziness is also given weightage on the procssed text field.
	
    				'''
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
				#A similar version of keyword case is considered for the image matching.
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
