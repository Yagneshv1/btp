#Code to perform text scraping for new institute website.

#Import the necessary libraries
import requests
from bs4 import BeautifulSoup
import re
import csv
import os
import json

visited = set()		#Set maintains the list of all the pages visited so far.
ignored_start = set()	#The sites from which the scraping is not taken forward
pages = 0		#Count of the number of pages that are scraped.
ignored_extensions = set(['png', 'jpeg', 'pdf', 'doc', 'jpg'])	#Page types not considered in text scraping
value = 0		#Count of pages visited that are in ignored extensions
failed_preprocess = 0	# Number of pages failed in the pre-processing step
num_links = 0		# Total number of page links
no_threshold = 0	# Count of pages failed scraping due to lack of threshold
out_domain = 0		#Count of pages visited out of domain during scraping
already_visit = 0	#Count of pages visited more than once during scraping
images = 0		#Count of the number of images.

def pre_process(site):
    '''
    Function to check if the site is a valid one to proceed for scraping
    '''
    global value
    #Check if the website is not an ignored extension and doesn't start with ignored urls
    if site.split('.')[-1].lower() in ignored_extensions:
        value += 1
        return False
    
    for k in ignored_start:
        if(site.startswith(k)):
            return False

    #Irrelevant pages for scraping text
    if site.__contains__("mailto") or site.__contains__("taxonomy") or site.__contains__("xml"): #Taxonomy pages and mailto pages have no content nor body so discard.
        return False

    #Contact pages are ignored for text scraping
    if site.endswith("contact"):
        return False
    
    return True

def scrape(site, count=30):
    '''
    Text Scraping for a site and redirecting to the next.
    '''
    global pages
    global num_links
    global no_threshold
    global out_domain
    global failed_preprocess
    global already_visit
    global images

    #print(pages)
    print("\n\n")

    #If there is no threshold for the page, return
    if(count == 0):
        no_threshold += 1
        return

    visited.add(site)	#Add the current page to visited set

    if(site.startswith("http:")):	#For http site connection issues occur so replace to https
        site = site.replace("http:", "https:")	

    #Check if the site passes the conditions to scrape.
    if not pre_process(site):
        failed_preprocess += 1
        return

    print("Extracting the page", site)
    try:
        r = requests.get(site, timeout=10)	#Get the site request
    except:
        return

    #Extract the HTML content of the page
    soup = BeautifulSoup(r.content, 'lxml')	#Parse HTML of page

    #Try to find the page title from potential divisions or classes as per HTML page pattern. Else the page link is considered as title.
    title = ''
    
    try:
        title = soup.find(class_="node-title").getText().strip()
    except:
        try:
            title = soup.find(class_="site-title").getText().strip()
        except:
            title = site

    #Replace slashes with other character to avoid misinterpreation of / as path seperator in filename.
    if title.__contains__("/"):
        title = title.replace("/", " ")

    #The text content in domain pages are enclosed in grid-x main-content class
    if site.__contains__("https://iitpkd.ac.in"):	#For pages in iitpkd we have main defined for the content except for the home page.
        if site not in ["https://iitpkd.ac.in", "https://iitpkd.ac.in/"]:
            soup = soup.find(class_="grid-x main-content")
    links = soup.find_all("a", href = True)			#Find the hyperlinks. 
	
    #Removing the header and footer sections. It could be a seperate tag or as a class.
    try:
        soup.header.decompose()
        soup.footer.decompose()
    except:
        pass
    
    try:
        element = soup.find(class_ = "header")
        print(element)
        if element:
            element.decompose()
        
        element = soup.find(class_ = "footer")
        if element:
            element.decompose()
    except:
        pass
    
    pages += 1
    print("Title of current extracted page is", title)
	
    message = ""
    #For pages of people, the entire content is extracted. For all others, only content in certain tags is considered.
    if site.startswith("https://iitpkd.ac.in/people"):
        message += soup.getText()
    else:
        content = soup.find_all(["p", "h1", "h2", "h3", "li", "ul", "br", "a"])	#All tags where we extract the content from.
        for k in content:						#Get the page content
            message += k.getText()
                        
    message = message.replace('\n', ' ')	#Replacing to remove the unnecessary \n from text

    #Collect all the hyperlink references in a page
    references = []
    for i in links:
        try:
            references.append(i['href'])
        except:
            continue

    #Creating and writing the json object
    json_obj = {"page_link" : site, "title" : title, "text": message, "hyperlinks": references}
    dump = json.dumps(json_obj)
    json_filename = str(pages) + title + ".json"
    
    with open(json_filename, "w") as outfile:
        outfile.write(dump)

	
    for j in references:	#Go through all the hyperlinks of the current page.
        if j.startswith("#"):
            continue
        num_links += 1
        
        if j.startswith(("/", "?")):	#For relative paths, 
            if j == "/":	#If its just /, its the same path. So, just ignore it by adding it to the visited set.
                j = site + "/"
                visited.add(j)
            elif j == "?page=0":
                j = site + j
                visited.add(j)
		    
	#Combine the URLs to handle relative and absolute paths directly
        j = requests.compat.urljoin(site, j)
			
        if j not in visited:			#Visit the pages which are not visited only within the institute domain.
            if j.__contains__('iitpkd') and not j.__contains__(".com"):	#For pages within the iitpkd domain, we have iitpkd name in the link.
                print('Redirecting to', j, 'from', site)
                scrape(j, count - 1)
            else:
                out_domain += 1
        else:
            already_visit += 1

if __name__ == "__main__":
    with open('urls_text.txt') as f:
        urls = f.read().split()

    URL = urls[0]
    #Add all ignored urls to visited so that they are not considered during the scraping chain.
    for u in urls[1:]:
        visited.add(u)
        ignored_start.add(u)
    
    HOME = os.getcwd()
    visited = set()		#Set maintaing the list of all the pages visited so far.
    os.mkdir("scraped_text")
    os.chdir(os.getcwd() + "/scraped_text")
    scrape(URL)
	
    #Print the important statistics
    print("The total pages scraped are", pages)
    print("The total number of file type pages", value)
    print(num_links/pages)
    print(no_threshold)
    print(out_domain)
    print(failed_preprocess)
    print(already_visit)
    print(len(visited))
