import requests
from bs4 import BeautifulSoup
import csv
import os
import json
import re

visited = set()		#Set maintaing the list of all the pages visited so far.
ignored_start = set()
pages = 0		#Keep count of number of pages that are scraped.
ignored_extensions = set(['png', 'jpeg', 'pdf', 'doc', 'jpg'])
value = 0
failed_preprocess = 0
num_links = 0
no_threshold = 0
out_domain = 0
already_visit = 0

def pre_process(site):
	global value
	if site.split('.')[-1] in ignored_extensions:	#Identify the type of url. If not file proceed.
		value += 1
		return False

	for k in ignored_start:	#If the url is a ignored skip it
		if(site.startswith(k)):
			return False

	if site.__contains__("mailto") or site.__contains__("taxonomy") or site.__contains__("xml"): #Taxonomy pages and mailto pages have no content nor body so discard.
		return False
	
	if site.endswith("contact"):	#Ignoring the contact pages
		return False
	return True

def scrape(site, count=10):
	global pages
	global num_links
	global no_threshold
	global out_domain
	global failed_preprocess
	global already_visit

	print(pages)
	print("\n\n")
	if(count == 0):		#Once we got the limit we simply return 
		no_threshold += 1
		return

	visited.add(site)	#Add the current page to visited

	if(site.startswith("http:")):	#For http site connection issues occur so replace to https
		site = site.replace("http:", "https:")	

	if not pre_process(site):
		failed_preprocess += 1
		return

	print("Extracting the page", site)	#Once possible go for scraping.
	try:
		r = requests.get(site, timeout=10)	#Get the site request
	except:
		return

	soup = BeautifulSoup(r.content, 'html.parser')	#Parse HTML of page

	try:	
		title = soup.find("title").getText()	#Try to get the title of page. Else simply the link used as site
	except:
		title = site

	if title.__contains__("/"):		#Avoid / in file name creation. So, just replace it with -
		title = title.replace("/", "-")

	if site.__contains__("https://iitpkd.ac.in"):	#For pages in iitpkd we have main defined for the content except for the home page.
		if site != "https://iitpkd.ac.in":
			soup = soup.find(id = "main")	#For homepage we need all links for redirection.
	
	message = ""
	pages += 1
	print("Title of current extracted page is", title)
	links = soup.find_all("a", href = True)			#Find the hyperlinks in the page
	
	if site.startswith("https://iitpkd.ac.in/people"):	#For faculty pages we need all the content in the page including the intro sections.
		message += soup.getText()
	else:
		content = soup.find_all(["p", "h1", "h2", "h3", "li", "ul"])	#All tags where we extract the content from.
		for k in content:						#Get the page content
			message += k.getText()
	
	message = message.replace('\n', ' ')	#Replacing to remove the unnecessary \n from text

	#Maintains the list of all the links in a page
	references = []
	for i in links:
		references.append(i['href'])

	num_links += len(references)
	#Creating and writing the json object
	json_obj = {"page_link" : site, "title" : title, "text": message, "hyperlinks": references}	#For each page we collect these details to put to ES
	dump = json.dumps(json_obj)
	
	json_filename = str(pages) + title + ".json"
	
	with open(json_filename, "w") as outfile:
		outfile.write(dump)

	
	for j in references:	#Go through all the hyperlinks of the current page.
		if j.startswith(("/", "?")):	#For relative paths, 
			if j == "/":	#If its just / its the same path. So, just ignore it by adding to visited set.
				j = site + "/"
				visited.add(j)
			elif j == "?page=0":
				j = site + j
				visited.add(j)
			else:
				regex = r".*//.*?(?=/)"	#Using regex to match the pages further having relative paths.
				try:
					match = re.search(regex, site)
					a = match.group(0)		#site == https://iitpkd.ac.in or https://resap.iitpkd.ac.in
					j = a + j
				except:
					j = site + j
			
		if j not in visited:			#Visit the pages which are not visited only.
			if j.__contains__('iitpkd'):	#For pages within the iitpkd domain, we have iitpkd name in the link.
				#if j.split('.')[-1] in ignored_extensions:
					#if j.endswith('.pdf') or j.endswith('.png') or j.endswith('.jpg') or j.endswith('.jpeg'):	#Skipping the filed pages.
				#	value = value + 1
				#	visited.add(j)
				#else:			#Else, extract the content
				print('Redirecting to', j, 'from', site)
				scrape(j, count - 1)
			else:
				out_domain += 1
		else:
			already_visit += 1

if __name__ == "__main__":
	with open('urls.txt') as f:
		urls = f.read().split()	#Urls has basically all the pages we skip and start page

	URL = urls[0]
	
	for u in urls[1:]:
		visited.add(u)
		ignored_start.add(u)

	HOME = os.getcwd()	#Create a directory to store scraped data
	os.mkdir("scraped")
	os.chdir(os.getcwd() + "/scraped")
	scrape(URL)	#Scrape started with first page given
	print("The total pages scraped are", pages)
	print("The total number of file type pages", value)
	print(num_links/pages)
	print(no_threshold)
	print(out_domain)
	print(failed_preprocess)
	print(already_visit)
	print(len(visited))
