#Now we need to convert the json files in folder to Ndjson object.

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
	textwords = nltk.word_tokenize(content.lower())
	textwords = [word for word in textwords if word.isalnum()]
	words_final = []
	for word in textwords:
		if word not in stops:
			words_final.append(word)
			
	processed_text = ' '.join(words_final)
	return processed_text

for filename in os.listdir(os.getcwd() + "/scraped_text"):
	if filename.endswith('.json'):
		with open("scraped_text/" + filename) as open_file:
			count += 1
			record = {"index" : {"_index" : "test1", "_id" : count}}
			result.append(json.dumps(record))
			inp = json.load(open_file)

			result.append(json.dumps(inp))
			#break

for k in result:
	print(k)
