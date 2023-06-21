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
- Front_end_test_version.py: Code implementation of the backend to implement various kinds of queries and features and the frontend streamlit interface code and ways to collect the evaluation results in test version.
- Image_Scraping_Newwebsite.py: Code implementation to scrape the images in the new institute website.
- Text_Scraping_OldWebsite.py: Code implementation for text scraping of old institute website.
- Text_processed_Dec13.out: Scraped text data from the old institute website as of Dec 13, 2022.
- Text_scraping_New website.py: Code implementation for text scraping from the new institute website.
- data.db: Database storing the login credentials of the users.
- evaluation_results.csv: Test Evaluation results collected.
- ignored_urls_image.txt: A text file containing the URLs that have been ignored during image scraping.
- ignored_urls_text.txt: A text file containing the URLs that have been ignored during text scraping.
- image_data_May4.out: Scraped image data from the new institute website as of May 4, 2023.
- image_json_ndjson.out: Python code to convert the json image files into a single ndjson object for indexing.
- synonyms.txt: File containing all the internal abbreviations and synonyms to consider during search.
- text_May5_updated.out: Scraped text data from new website as of May 5, 2023.
- text_json_ndjson.out: Python code to convert the json text files into a single ndjson object for indexing.


## Usage
Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Support
For support please reach out to 111901027@smail.iitpkd.ac.in or 111901014@smail.iitpkd.ac.in

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.


## Authors and acknowledgement

- Dr. Koninika Pal(Mentor)
- Katragadda Yagnesh(Team Member)
- Bandaru Rupesh Rahul(Team Member)


## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
