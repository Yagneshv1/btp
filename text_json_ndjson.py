#Code implementation to convert the JSON text files into a single ndjson object.

#Importing the required nltk libraries for pre-processing
import os
import json
import nltk
nltk.download('punkt')
from nltk import word_tokenize
from nltk.corpus import stopwords
nltk.download('stopwords')
from nltk.stem import WordNetLemmatizer
nltk.download('wordnet')
count = 0

result = []

stops = set(stopwords.words("english"))
lm= WordNetLemmatizer()

def pre_process(content):
	'''
 	Function to pre-process the input content. Involves lowercasing, stopword removal, non-alphanumeric characters removal
 	'''
	textwords = nltk.word_tokenize(content.lower())
	textwords = [word for word in textwords if word.isalnum()]
	words_final = []
	for word in textwords:
		if word not in stops:
			words_final.append(word)
			
	processed_text = ' '.join(words_final)
	return processed_text

#For each file in the directory where text scraped files are stored, we pre-process and append to the result which is finally converted to json.
for filename in os.listdir(os.getcwd() + "/scraped_text"):
	if filename.endswith('.json'):
		with open("scraped_text/" + filename) as open_file:
			count += 1
			record = {"index" : {"_index" : "test1", "_id" : count}}
			result.append(json.dumps(record))
			inp = json.load(open_file)
			result.append(json.dumps(inp))

#Output shall be redirected to a .out file
for k in result:
	print(k)
