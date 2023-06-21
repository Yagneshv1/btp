#Code implementation to convert the json image files to ndjson object

#Import the necessary NLTK libraries for pre-processing
import os
import json
import nltk
nltk.download('punkt')
from nltk import word_tokenize
from nltk.corpus import stopwords
nltk.download('stopwords')
from nltk.stem import WordNetLemmatizer
nltk.download('wordnet')

result = []
stops = set(stopwords.words("english"))
lm= WordNetLemmatizer()

#Perform the operation for each image file.(Each image is stored as JSON file after scraping)
for filename in os.listdir(os.getcwd() + "/scraped_2_gallery"):
	if filename.endswith('.json'):
		with open("scraped_2_gallery/" + filename) as open_file:
			#Read the contents of the file
			inp = json.load(open_file)
			#Extract the image description which is then pre-processed
			text_content = inp['image_desc']
			textwords = nltk.word_tokenize(text_content.lower())
			textwords = [word for word in textwords if word.isalnum()]
			words_final = []
			for word in textwords:
				if word not in stops:
					words_final.append(word)
			
			processed_text = ' '.join(words_final)
			
			#Store the pre-processed image description along with the original description.
			inp['processed_desc'] = processed_text
			result.append(json.dumps(inp))

for k in result:
	print(k)
