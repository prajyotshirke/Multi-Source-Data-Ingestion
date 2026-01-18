## Phase 1: Problem Understanding 

### What was I asked to build?

**Task:** Multi-source data ingestion pipeline

**Requirements:**

- Fetch from 3 different sources (API, file, web)
- Normalize all to common JSON format
- Handle errors gracefully
- Write tests
- Code must be reusable

### Key Questions I Asked Myself:

**Rationale for Three Data Sources:**

**To expose the system to diverse failure modes**: 
- Network issues (API), file structure errors (CSV), and content parsing problems (web scraping/HTML).
- Real-world data pipelines typically integrate information from various formats.
  
**Effective Error Management:**
- The system should be robust and not fail entirely when encountering corrupted data.
- Implement retries for temporary issues (like network blips) but fail immediately for critical, non-recoverable errors (like misconfiguration).
- Comprehensive logging is essential for subsequent debugging and troubleshooting.
  
**Why Standardize on JSON?**
- JSON offers a universal, language-independent data exchange format.
- It is easily importable into various platforms, including databases, data analysis libraries (e.g., Pandas), or other APIs.
- It simplifies the data flow by consolidating disparate source formats.
  
**Achieving Code Reusability:**
- Employ a base class with a standardized interface (using inheritance).
- Ensure every data fetching component adheres to and implements the same set of required methods.
- The main orchestration logic (Main.py) should be decoupled, operating solely on the common interface without needing to know the specifics of each fetcher's implementation.

### Output of Phase 1:

Clear understanding: I'm building a data pipeline with modular fetchers and centralized orchestration.

---

## Phase 2: Architecture Breakdown 

### How should I structure this?

**Option 1: Monolithic** (Wrong)

```python
# One big file with all logic mixed together
def main():
    # Fetch from API
    # Fetch from CSV
    # Fetch from Web
    # Normalize
    # Save
```

**Problem:** Can't reuse. Can't test. Can't add new source without editing main().

**Option 2: Factory Pattern** (Better)

```python
class FetcherFactory:
    def get_fetcher(source_type):
        if source_type == "api": return APIFetcher()
        if source_type == "csv": return CSVFetcher()
```

**Problem:** Still couples main logic to factory.

**Option 3: Base Class + Composition** ( Chosen)

```python
class BaseFetcher:
    def fetch(self): pass  # Every fetcher implements this

class NewsAPIFetcher(BaseFetcher):
    def fetch(self): ...

class CSVFetcher(BaseFetcher):
    def fetch(self): ...
```

**Advantage:** Each fetcher is independent, testable, and new sources are just new classes.

### Final Architecture

```
multi-source-ingestion/
├── fetchers/
│   ├── common.py              # Base class + shared utilities
│   ├── newsapi.py             # Implements BaseFetcher for API
│   ├── csv_reader.py          # Implements BaseFetcher for CSV
│   ├── web_scraper.py         # Implements BaseFetcher for web
│   └── models.py              # Pydantic schema (Article class)
├── main.py                    # Orchestrates: fetch + normalize + save
├── tests/
│   ├── test_newsapi.py       # Unit tests for each fetcher
│   ├── test_csv.py
│   ├── test_scraper.py
│   └── test_main.py          # Integration test
└── sample_data.csv           # Test data
```

**Why this structure?**

- **Single Responsibility:** Each file has one job
- **Testable:** Can mock each fetcher independently
- **Extensible:** New source = new file, no existing code changes
- **Follows real patterns:** Mirrors how Netflix/Uber structure data pipelines

---

#### Phase 3: Prompt Planning , Prompts Used with AIPrompt 1:

**Base Class Design**

My prompt:"Develop a foundational Python class for components that retrieve data.

**This class must:**
- Define an abstract fetch() method.
- Incorporate a mechanism for retries with exponential backoff, specifically limited to network-related failures.
- Include a private method, \_normalize_article(), responsible for input validation.
- Utilize custom-defined exception classes.
- Implement logging functionality.
- Be designed to facilitate easy testing using mocks."

**AI response:** Satisfactory (Accepted with minor revisions)**

**My modifications:** Incorporated additional explanatory comments and improved the separation of different responsibilities within the code.

**Why this worked:** Specific request, clear requirements, mentioned constraints (testable)

---

#### Prompt 2: NewsAPI Fetcher Analysis

**Original Request:"Write a NewsAPI fetcher that extends BaseFetcher:**
- Fetch articles about India using API key from env
- Handle 401 (auth), 429 (rate limit), timeout, malformed JSON separately
- For auth/malformed: fail immediately (don't retry)
- For timeout/429: use retry logic from base class
- Return empty list if source fails (don't crash)
- Log all errors"

**AI Output:** Satisfactory (Accepted with minor adjustments)

**Refinement:** I incorporated a clear distinction between persistent and temporary errors.

**Effectiveness:** The prompt's success stemmed from its explicit outlining of different error scenarios and the required handling strategy for each one.-----The subsequent section offers an examination of a prompt and its refinement process concerning a CSV file reading task.

#### Scenario 3: CSV Data Fetcher

**Original Request:"Create a CSV reading function with the following requirements:**
- Graceful handling of a 'file not found' error (should return an empty list instead of crashing).
- Robust encoding error handling (attempt UTF-8 first, then fallback to latin-1).
- Mandatory validation of key columns: 'title', 'content', 'url'.
- Logic to skip rows that are completely empty.
- Logic to skip rows with missing mandatory fields (log the error and proceed).
- The final output must be structured according to an 'Article' data schema."

**Initial AI Output: Needed minor adjustments.**

**Modifications Made:** Enhanced the encoding fallback mechanism and included the row number in error logs for better debugging.

**Rationale for Changes**: Required a more explicit and robust strategy for managing file encoding issues.

---

**This section outlines the requirements for a web scraping script.**

#### Prompt 4: Web Scraper

**Requested features:**
- **Target website**: BBC News.
- **Connection timeout**: 10 seconds.
- **Error handling**: Retry mechanism for network failures; do not retry on parsing errors.
- **Request etiquette**: Implement a 1-second delay between consecutive requests (for ethical scraping).
- **Structure robustness**: If the HTML structure is altered (resulting in no articles being found), the function should return an empty list.
- **Parsing tool**: Utilize BeautifulSoup to extract information from "h2" tags that contain a data-testid attribute.
- **Header:** Include a User-Agent string in the request headers.

**AI response:** Good

**What I tweaked:** Added fallback HTML selector, improved error messages

---

#### Prompt 5: Testing Strategy

**The Request:"Generate pytest tests for a NewsAPI data retrieval component, including the following scenarios:**
- Verification of a successful data fetch.
- Handling of a timeout error, which should trigger a retry.
- Response to a 401 Unauthorized error, which should not trigger a retry.
- Handling of a 429 Rate Limit error, which should trigger a retry.
- Testing with a corrupted or incorrectly formatted JSON response.
- Validation of output structure (ensuring all required fields are present and correctly normalized).
- Utilize mocking techniques to simulate various API responses.
- The tests must not make actual external API calls."

**AI response:** Excellent

**What I tweaked:** Nothing major, just improved comments

---

**Why This Prompting Strategy Was Effective**
- Specificity: Instead of a general request like "write a web scraper," the prompt was specific: "write a web scraper for BBC News that..."
- Defined Constraints: Timeouts, error handling, and rate limits were clearly stated.
- Testability: The request specifically asked for code that was mockable for testing.
- Iterative Approach: Each subsequent prompt was a refinement or build on the previous output.
- Pre-Planning (Evidence of Thinking): The desired outcome was fully conceptualized before engaging the AI.

---

## Phase 4: Implementation 

### What Actually Happened vs What I Planned

**Planned:** 1 hour per fetcher, 1 hour testing, 1 hour integration

**Reality:**

- NewsAPI: 45 min (straightforward)
- CSV: 1.5 hours (encoding issues!)
- Web scraper: 2 hours (HTML structure varies, needed fallbacks)
- Testing: 1.5 hours (mocking was trickier than expected)

### Key Moments

**Moment 1: Integrating the NewsAPI**

**Process:**
- The implementation went smoothly.
- The predictability of the REST API simplified the workflow:
- Initiate Request $\rightarrow$ Receive JSON Data $\rightarrow$ Parse and Standardize Data
- The clear, standardized error codes (401, 429, 500) provided a straightforward strategy for error handling.
- Key Insight: Utilizing a REST API proved to be less complex than alternative methods like direct file input/output or web scraping.

---

#### Moment 2: CSV Encoding Error

**First attempt failed:**

```python
with open(self.file_path, 'r') as f:
    reader = csv.DictReader(f)
```

**Issue: The system experienced a crash when processing files that were not encoded in UTF-8 (specifically, Latin-1 text).**

**Fix:** Implement a strategy to attempt decoding the file using multiple encodings.
for encoding in ['utf-8', 'latin-1', 'iso-8859-1']:

**try:**# Attempt to read the file content with the current encoding

**except UnicodeDecodeError:**

**continue** # If decoding fails, move on to the next encoding

**Key Takeaway:** File encoding mismatches are a common issue in data pipelines. It is crucial to build in robust fallback mechanisms to handle different encodings gracefully.

---

#### Moment 3: Handling Changes in HTML for Web Scraping

**Initial Approach:**
- articles = soup.find_all('h2', {'data-testid': True})
- Issue: BBC frequently updates its HTML structure, causing specific selectors to become unreliable.

**Revised Strategy:**
- Implement multiple, sequential selectors as fallbacks.
- article_elements = soup.find_all('h2', {'data-testid': True})

**if not article*elements:**
- article_elements = soup.find_all('a', class*='sc-4fedabbc-3')

**Learning:** Web scraping requires defensive programming. Always have backups.

---

#### Moment 4: Testing Mocking

**First attempt:**

```python
@patch('requests.get')  #  Wrong
def test_fetch(self, mock_get):
```

**Problem:** Used an incorrect import path for mocking.

**Solution:**
- The mocking should target the location where the object is being used, not where it is originally defined.
- @patch('fetchers.newsapi.requests.get') # Correct import path for the mock
- def test_fetch(self, mock_get): # test logic here
  
**Learning:** Successful mocking depends on correctly identifying the import path. The key question is: "From what location does the code under test import the dependency (X)?"

---

### Iterations That Failed (and why)

**Attempt 1: Global Retry Decorator Approach**

**Initial Strategy:**
@retry(max_attempts=3, backoff=2)
def fetch_from_api(self):
...
**Issue:** The decorator couldn't distinguish between error types (it shouldn't retry a 401 Unauthorized error, but should retry a timeout).

**Resolution:** The retry mechanism was relocated into the method bodies to allow for distinct handling based on the error type.

**Takeaway:** While decorators are suitable for straightforward retry scenarios, more complex or conditional retry logic requires explicit, in-method implementation.

---

**Iteration 2: Consolidated Normalization Function**

**Attempt:**
def normalize(data: dict) -> Article:

    # Handles all sources


**Issue:** Data sources exhibit diverse structures (e.g., NewsAPI uses a .description field, while CSV data does not).

**Approach:** Implement source-specific normalization within each fetcher before applying a shared validation process.

**Key Insight:** Data normalization is unique to each source, whereas data validation remains independent of the source.

---

**Iteration 3: Attempting Comprehensive News Scraping**

**Initial Goal:** Scrape 50 articles from BBC.

**Issue Encountered:** The process was excessively slow (50 articles x 1 second delay = 50 seconds total) and risked triggering server blocking.

**Revised Strategy:** The scraping volume was reduced to 5 articles, and specific delays were implemented with clear justification.

**Key Takeaway:** Adhering to responsible production ethics is crucial. Treat the servers being scraped with respect.


---

## Phase 5: Error Handling Strategy 

### The Strategy

| Error                 | Cause              | Strategy                           | Why                                  |
|-----------------------|--------------------|------------------------------------|--------------------------------------|
| Timeout               | Network blip       | Retry 3x with exponential backoff  | Usually temporary, retry works       |
| 401 Unauthorized      | Bad API key        | Fail immediately, log              | Config issue, won't fix with retries |
| 429 Too Many Requests | Rate limit         | Retry after delay                  | Temporary, might be freed up later   |
| Connection refused    | Network down       | Retry                              | Transient                            |
| Malformed JSON        | Bad API data       | Skip article, continue             | Don't crash whole pipeline           |
| File not found        | Missing CSV        | Return empty list                  | Graceful degradation                 |
| Bad encoding          | Old system data    | Try multiple encodings             | Common in enterprises                |
| HTML parse error      | Structure changed  | Skip + log                         | Scraping is fragile                  |


### Why NOT Other Strategies

**Strategy Options for Error Handling:**
- Continuous Retries: Retrying perpetually on specific errors like 401s is inefficient and unhelpful.
- Immediate Failure: A single faulty input file (e.g., a bad CSV) could abruptly terminate the entire process.
- Error Suppression: Ignoring failures leads to issues that are difficult to trace and resolve later.
- Intelligent Retries and Resilience: Employing varied strategies based on the error type to attempt recovery and allow the pipeline to continue operating, even with minor issues.



### Production Relevance

- Authentication failures should not be retried. Log the error and proceed without delay.
- Rate limits are temporary. Implement a waiting period followed by a retry.
- Transient network issues are common. Utilize exponential backoff for retries.
- Accepting partial results is better than complete failure. Prioritize a subset of successful operations (e.g., 8 out of 10) over a complete stop (0 out of 10).


---

## Phase 6: Reusability Test

### Can I Add a 4th Source?

**Requirement:** Ensure the design is testable and demonstrate that adding a fourth data source requires minimal code modifications.

**Hypothetical Example:** Integrate a Twitter data retrieval component.

**Necessary Modifications:**
- Create fetchers/twitter.py.
- Subclass BaseFetcher and implement the abstract fetch() method.
- Add two lines of code to main.py.
  
**Result:** Only these changes are needed, with no alteration to existing source code.


**In main.py, add the following 2 lines:**

from fetchers.twitter import TwitterFetcher

twitter_fetcher = TwitterFetcher()  # Instantiation
all_articles.extend(twitter_fetcher.fetch())  # Data aggregation

**Conclusion:** The established architecture supports the addition of an arbitrary number of sources.




---

## Phase 7: What I Learned

### Technical Learnings
- Data harmonization is more challenging than data retrieval
- Disparate sources often use different field names or formats.
- The error management approach is vital
- The distinction between errors that trigger a retry and those that cause failure dictates the pipeline's robustness.
- Mocking requires knowing the import structure
- The @patch() decorator's path must point to where the code imports the item, not where the item is originally defined.
- CSV character encoding is a major factor - many legacy systems employ Latin-1, necessitating support for alternate encodings.
- Web scraping demands redundancy - HTML structures frequently change, making fallback selectors essential.
- Effective logging is indispensable
- High-quality logs accelerated debugging significantly.


### Engineering Learnings

**Prioritize Architectural Design**

- The fundamental structure (e.g., using a base class, factory pattern, or a monolithic structure) is more critical than the fine details of code quality.
  
**Continuous Testing**
  
- Adopting a Test-Driven Development (TDD) approach, where tests are written alongside code, is more efficient than writing tests retrospectively.
  
**Ensure Resilience**

- A system or pipeline that can process most data (e.g., 80%) while handling failures is superior to one that fails completely when encountering an issue.
  
**Maintain Single Responsibility**

- Every module or class should be dedicated to a single, well-defined function or concern.
  
**Favor Clarity Over Complexity**

- Logic that is simple and easy to read, such as explicit retry mechanisms, is preferable to complex, "magical" shortcuts like hidden decorators.


### What I'd Do Differently

**Prioritize testing**

- Implementing tests from the outset would have revealed encoding problems sooner.
  
**Implement mocking earlier**

- This would have allowed me to discover the incorrect import path much earlier in development.
  
**Opt for a standard dataclass over Pydantic initially**

- Pydantic's complexity was unnecessary for the current scope.
  
**Build in rate-limit awareness from the beginning**

- The experience with BBC scraping highlighted the need to integrate rate limit handling earlier.


## Phase 8: Production Considerations

### What's Missing That Real Pipelines Have

**Not included (beyond scope):**

- Database persistence
- Async fetching (all sources fetch serially)
- Monitoring/alerting
- Configuration management
- Data quality checks
- Deduplication

 **Included (production-ready):**
- Strategy for handling errors
- Implementation of retry logic, including exponential backoff
- Comprehensive logging procedures
- Validation of data schemas
- Mechanisms for graceful service degradation
- Implementation of unit and integration testing

### If This Were Real

**What I'd add next:**

**Concurrent Data Retrieval:** Implement simultaneous fetching from all three data sources.

**Persistent Storage:** Transition from storing data in a JSON file to using a PostgreSQL database.

**Performance Tracking:** Establish a monitoring system to track the success rate individually for each source.

**Failure Notification:** Set up an alerting mechanism to notify personnel if any single data source experiences an outage lasting one hour or more.

**Uniqueness Enforcement:** Implement a deduplication process to prevent storing the same news article more than once.

O**ptimized Fetching**: Introduce rate limit awareness by caching results and minimizing redundant data requests.


---

## Final Checklist: Did I Meet Requirements?

### Evaluation Criteria Checklist

 **Error handling for each source?**
**NewsAPI:** Includes timeout and retry mechanisms, with authentication attempts not being retried, and a rate limit retry.

**CSV:** Incorporates encoding fallback and handles cases of missing files or columns.

**Web:** Features network timeout and retry, and skips data on parsing errors.

**Tests have confirmed the effectiveness of each strategy.**


 **Output normalized?**
**Standardized Data Schema:** All sources must include the same five fields (title, content, source, url, fetched_at).

**Data Integrity:** Ensure no null values. Use "N/A" specifically for any missing URL fields.

**Time Format**: All timestamps must adhere to the ISO 8601 standard.

**Schema Enforcement:** Pydantic is used to validate and enforce the data structure.

 **Tests written?**
- 8 NewsAPI tests
- 7 CSV tests
- 7 Web tests
- 5 integration tests
- All test edge cases covered


 **Why this error strategy?**

**Error Handling Strategy:**
- Adopt varied approaches for different types of errors.
- Implement retry logic only for temporary errors; immediately halt processing upon encountering irreversible errors.
- Ensure comprehensive logging for all events to aid in troubleshooting.


 **Code reusable?**
- The BaseFetcher establishes the required interface.
- Adding a new source requires one new file and two lines of code in main.py.
- Fetcher implementations are independent of each other.
- The tests are designed to work with any source.


---

## What I Explained Well

- Architecture decisions (base class over factory)
- Error handling strategy (retry vs fail fast)
- Testing philosophy (mock external dependencies)
- CSV encoding handling (real problem, practical solution)

## What Could Be Better

- More performance optimization (async would help)
- More detailed logging (debug mode)
- Configuration management (env vars only)
- Data quality metrics

---

## Conclusion

**Developed**: Multi-source data ingestion pipeline capable of handling data from 3 distinct sources, each with unique error patterns.

**Insight Gained**: The effectiveness of data normalization and error handling strategies is more critical than the sheer volume of code written.

**Skills Demonstrated**: Implemented production-ready system patterns, including graceful degradation, intelligent retries, strict schema validation, and extensive testing.

**Future-Proofing:** The architecture is designed for unlimited scalability and is immediately ready to integrate source #4 with minimal code modifications.


```



