# B.Tech Project(BTP)

## Name
Smart Search Engine to Handle Phrase Queries

## Description
This project implements a search engine using BeautifulSoup, Elastic Search, Streamlit Frameworks for IIT Palakkad Institute website which supports various types of queries like
- Keyword Search
- Phrase Queries
- Quotes Queries
- Image Queries

The other significant features of the project include
- Snippet Generation
- Highlighting the matches
- Fuzziness
- Actual Image Rendering
- Synonyms and Abbreviations

## File Organisation

The contents of the files in this repository are as follows:
- Front_end_test_version.py: Code implementation of the backend to implement various kinds of queries and features and the frontend Streamlit interface code and ways to collect the evaluation results in the test version.
- Image_Scraping_Newwebsite.py: Code implementation to scrape the images in the new institute website.
- Text_Scraping_OldWebsite.py: Code implementation for text scraping of old institute website.
- Text_processed_Dec13.out: Scraped text data from the old institute website as of Dec 13, 2022.
- Text_scraping_New website.py: Code implementation for text scraping from the new institute website.
- data.db: Database storing the login credentials of the users.
- evaluation_results.csv: Test Evaluation results collected.
- ignored_urls_image.txt: A text file containing the URLs that have been ignored during image scraping.
- ignored_urls_text.txt: A text file containing the URLs that have been ignored during text scraping.
- image_data_May4.out: Scraped image data from the new institute website as of May 4, 2023.
- image_json_ndjson.out: Python code to convert the JSON image files into a single ndjson object for indexing.
- synonyms.txt: File containing all the internal abbreviations and synonyms to consider during the search.
- text_May5_updated.out: Scraped text data from the new website as of May 5, 2023.
- text_json_ndjson.out: Python code to convert the JSON text files into a single ndjson object for indexing.


## Support
For support please reach out to 111901027@smail.iitpkd.ac.in or 111901014@smail.iitpkd.ac.in

## Roadmap
The new features that could be incorporated into the project are as follows:
- Document Search
- Advanced scoring models incorporating the context of the content.
- Complete image search instead of text-to-image search.
- PageRank feature shall be incorporated into scoring.


## Authors and acknowledgement

- Dr. Koninika Pal(Mentor)
- Katragadda Yagnesh(Team Member)
- Bandaru Rupesh Rahul(Team Member)


## Project status
The project is currently under a test version. The parameters may be tuned based on the analysis of results and the production version may be released.
