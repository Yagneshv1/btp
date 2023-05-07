#Now we need to convert the json image files in folder to Ndjson object.

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

for filename in os.listdir(os.getcwd() + "/scraped_2_gallery"):
	if filename.endswith('.json'):
		with open("scraped_2_gallery/" + filename) as open_file:
			# count += 1
			# record = {"index" : {"_index" : "test_image", "_id" : count}}
			# result.append(json.dumps(record))
			inp = json.load(open_file)
			text_content = inp['image_desc']
			textwords = nltk.word_tokenize(text_content.lower())
			textwords = [word for word in textwords if word.isalnum()]
			words_final = []
			for word in textwords:
				if word not in stops:
					words_final.append(word)
			
			processed_text = ' '.join(words_final)
			inp['processed_desc'] = processed_text
			result.append(json.dumps(inp))

for k in result:
	print(k)
