import requests
from bs4 import BeautifulSoup
import re
import csv
import os
import json

url_re = r'https://(.*?)/'
url_pattern = re.compile(url_re, flags=re.DOTALL)

class ImageScraper:
    def __init__(self, link, title):
        self.image_dict = {}
        self.pagelink = link
        self.title = title
    
    def extract_text(self, a, header_string):
        for k in a:
            soup = BeautifulSoup(k[0], 'lxml')
            if k[1].startswith("/"):
                try:
                    b = url_pattern.findall(self.pagelink)[0] + k[1]
                    k = (k[0], b)
                except:
                    b = self.pagelink + k[1]
                    k = (k[0], b)
            try:
                x = self.image_dict.get(k[1])
                x[1] += soup.getText()
                self.image_dict[k[1]] = [x[0], x[1]]
            except:
                self.image_dict[k[1]] = [header_string, soup.getText().strip()]

    def extract_text_regex(self, inp, header_string):
        r1 = r'(<p>.*?<img.*?src="(.*?)")'
        r2 = r'(<li>.*?<img.*?src="(.*?)")'
        r3 = r'(<ul>.*?<img.*?src="(.*?)")'
        r4 = r'(<br>.*?<img.*?src="(.*?)")'
        r9 = r'(<a>.*?<img.*?src="(.*?)")'

        r5 = r'(<img.*?src="(.*?)".*?</p>)'
        r6 = r'(<img.*?src="(.*?)".*?</li>)'
        r7 = r'(<img.*?src="(.*?)".*?</ul>)'
        r8 = r'(<img.*?src="(.*?)".*?</br>)'
        r10 = r'(<img.*?src="(.*?)".*?</a>)'

        prev_pattern_1 = re.compile(r1, flags=re.DOTALL)
        prev_pattern_2 = re.compile(r2, flags=re.DOTALL)
        prev_pattern_3 = re.compile(r3, flags=re.DOTALL)
        prev_pattern_4 = re.compile(r4, flags=re.DOTALL)
        prev_pattern_5 = re.compile(r9, flags=re.DOTALL)

        next_pattern_1 = re.compile(r5, flags=re.DOTALL)
        next_pattern_2 = re.compile(r6, flags=re.DOTALL)
        next_pattern_3 = re.compile(r7, flags=re.DOTALL)
        next_pattern_4 = re.compile(r8, flags=re.DOTALL)
        next_pattern_5 = re.compile(r10, flags=re.DOTALL)

        a = []
        try:
            a += prev_pattern_1.findall(inp)
            s = a[0]
            self.extract_text(a, header_string)
        except:
            a = []
            a += prev_pattern_2.findall(inp)
            a += prev_pattern_3.findall(inp)
            a += prev_pattern_4.findall(inp)
            a += prev_pattern_5.findall(inp)
            self.extract_text(a, header_string)

        a = []
        try:
            a += next_pattern_1.findall(inp)
            s = a[0]
            self.extract_text(a, header_string)
        except:
            a = []
            a += next_pattern_2.findall(inp)
            a += next_pattern_3.findall(inp)
            a += next_pattern_4.findall(inp)
            a += next_pattern_5.findall(inp)
            self.extract_text(a, header_string)
            
    
    def scrape(self):
        r = requests.get(self.pagelink, timeout=10)	#Get the site request
        
        soup = BeautifulSoup(r.content, 'html.parser')	#Parse HTML of page
        #Taking out the main content of the HTML page and convert to string after removing the title block.
        html = None
        if not self.pagelink == "https://iitpkd.ac.in" or self.pagelink == "https://iitpkd.ac.in/":
            try:
                html = soup.find(class_="grid-x main-content")
            except:
                html = soup

        try:
            element = html.find("div", id="block-iitpkd-page-title")
            if element:
                element.decompose()
        except:
            html = soup

        #Removing the header and footer
        try:
            html.header.decompose()
            html.footer.decompose()
        except:
            pass

        try:
            element = html.find(class_ = "header")
            if element:
                element.decompose()
            element = html.find(class_ = "footer")
            if element:
                element.decompose()
        except:
            pass
        
        string_content = str(html)
        #print(string_content)
        #Now, we need to get the HTML with the required header area. This will give all the images and their block areas
        header_re = r"(<h\d.*?>(.*?)</h\d.*?<img.*?)(?=<h)|(<h\d.*?>(.*?)</h\d.*?<img.*)"
        header_pattern = re.compile(header_re, flags=re.DOTALL)
        content = header_pattern.findall(string_content)
        
        #print('The length is', len(content))
        if len(content) == 0:
            #Case when no headers are there just the page and image. In this just take the entire page into consideration.
            self.extract_text_regex(string_content, self.title)

        else:
            #When we are able to capture the headers
            for i in content:
                if i[0] == '':
                    self.extract_text_regex(i[2], i[3])
                else:
                    self.extract_text_regex(i[0], i[1])
                
        return self.image_dict

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
images = 0

def pre_process(site):
    global value
    if site.split('.')[-1].lower() in ignored_extensions:
        value += 1
        return False
    
    for k in ignored_start:
        if(site.startswith(k)):
            return False

    if site.__contains__("mailto") or site.__contains__("taxonomy") or site.__contains__("xml"): #Taxonomy pages and mailto pages have no content nor body so discard.
        return False
	
    if site.endswith("contact"):
        return False
    
    return True

def scrape(site, count=30):
    global pages
    global num_links
    global no_threshold
    global out_domain
    global failed_preprocess
    global already_visit
    global images

    #print(pages)
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

    print("Extracting the page", site)
    try:
        r = requests.get(site, timeout=10)	#Get the site request
    except:
        return
    
    soup = BeautifulSoup(r.content, 'html.parser')	#Parse HTML of page
    title = ''
    try:
        title = soup.find(class_="node-title").getText().strip()
    except:
        try:
          title = soup.find(class_="site-title").getText().strip()
        except:
            title = site

    if title.__contains__("/"):		#Avoid / in file name creation. So, just replace.
        title = title.replace("/", " ")

    if site.__contains__("https://iitpkd.ac.in"):	#For pages in iitpkd we have main defined for the content except for the home page.
        if site != "https://iitpkd.ac.in" and site != "https://iitpkd.ac.in/" and site != "https://iitpkd.ac.in/hi":
            soup = soup.find(id = "block-iitpkd-content")	#For homepage we need all links for redirection.
	
    pages += 1
    print("Title of current extracted page is", title)

    images_desc = {}

    if site not in ["https://iitpkd.ac.in/gallery", "https://iitpkd.ac.in/faculty-list", "https://iitpkd.ac.in/adjunct-faculty", "https://iitpkd.ac.in/research-scholars-list", "https://iitpkd.ac.in/staff-list", "https://iitpkd.ac.in/pmrf"]:
        a = ImageScraper(site, title)
        images_desc = a.scrape()
	
    links = soup.find_all("a", href = True)			#Find the hyperlinks.

	#Maintains the list of all the links in a page
    references = []
    for i in links:
        references.append(i['href'])

	#Creating and writing the json object
    for k,v in images_desc.items():
        images += 1
        
        json_obj = {"page_link" : site, "title" : title, "hyperlinks": references, "image_link" : k, "image_desc" : v[1].replace("\n", " "), "section" : v[0]}
        dump = json.dumps(json_obj)
        
        json_filename = str(images) + title + ".json"
        
        with open(json_filename, "w") as outfile:
            outfile.write(dump)

	
    for j in references:	#Go through all the hyperlinks of the current page.
        if j.startswith("#"):
            continue
        num_links += 1
        
        if j.startswith(("/", "?")):	#For relative paths, 
            if j == "/":	#If its just / its the same path. So, just ignore it by adding to visited set.
                j = site + "/"
                visited.add(j)
            elif j == "?page=0":
                j = site + j
                visited.add(j)

        j = requests.compat.urljoin(site, j)
			
        if j not in visited:			#Visit the pages which are not visited only.
            if j.__contains__('iitpkd') and not j.__contains__(".com"):	#For pages within the iitpkd domain, we have iitpkd name in the link.
                print('Redirecting to', j, 'from', site)
                scrape(j, count - 1)
            else:
                out_domain += 1
        else:
            already_visit += 1

if __name__ == "__main__":
    with open('urls.txt') as f:
        urls = f.read().split()

    URL = urls[0]
	
    for u in urls[1:]:
        visited.add(u)
        ignored_start.add(u)
    
    HOME = os.getcwd()
    visited = set()		#Set maintaing the list of all the pages visited so far.
    os.mkdir("scraped_2_gallery")
    os.chdir(os.getcwd() + "/scraped_2_gallery")
    scrape(URL)
    print("The total pages scraped are", pages)
    print("The total number of file type pages", value)
    print(num_links/pages)
    print(no_threshold)
    print(out_domain)
    print(failed_preprocess)
    print(already_visit)
    print(len(visited))