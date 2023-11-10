## Pradeep's Comments
Things I would do if I had extra time:
1. *Security and Authorization*: Implement Role-Based Access Control (RBAC) to ensure that only authorized and authenticated users can access the API. Utilize authentication middleware to handle user identity and permissions.
2. *Data Storage and Security*: Enhance data security by implementing encryption at rest using cloud services like AWS Key Management Service (KMS) or similar solutions to protect sensitive information.
3. *Data Storage*: Replace the local pandas dataframe with a more scalable and robust solution. Consider storing data in a Data Lake, object store (e.g., AWS S3), a Key-Value database (e.g., MongoDB), or a relational database for better data management and scalability.
4. *Scalability and Performance*: Implement the Command Query Responsibility Segregation (CQRS) pattern to separate read and write operations. Distribute queries and inserts to different shards or nodes, enhancing scalability and performance.
5. *Big Data Processing*: Integrate with Big Query for querying large datasets efficiently. Utilize PySpark to handle big data scenarios, acknowledging the potential growth in dataset size in real-world scenarios.
6. *Microservices Architecture*: Transform the REST API into a microservice architecture. Make the API stateless, allowing it to be hosted behind a load balancer. This enables any instance to handle queries or inserts, enhancing scalability and fault tolerance.
7. *Health Checks*: Implement health checks for the REST API. This ensures that the API Gateway can skip non-responsive nodes, improving overall system reliability.
8. *Pagination Support*: Introduce pagination support for better handling of large result sets. This helps in improving response times and resource utilization.
9. *Framework and Tooling Upgrade*: Consider migrating to a more modern framework like FastAPI, leveraging Pydantic's BaseModel for improved data validation and serialization.
10. *API Contract Refinement*: Enhance the API contracts for both POST and GET requests. Clearly define request and response formats, error handling, and any constraints for clients consuming the API.
11. *Exception Handling Middleware*: Implement middleware for exception handling to provide consistent error responses and enhance the overall robustness of the API. This ensures better developer experience and easier troubleshooting.
12. *Logging to ELK or Splunk*: Implement logging to ELK (Elasticsearch, Logstash, Kibana) or Splunk for comprehensive monitoring and analysis of production logs. This enables effective troubleshooting, performance analysis, and insights into the system's behavior in a production environment.
13. *Testing capability*: Implement unit test case per class instead of togather. Implement BDD using behave. Implement System test using postman or selenium
14. *Continuous Integration and Deployment (CI/CD)*: Implement CICD pipelines using Jenkins, CircleCI, Github Actions, Bamboo etc


# ipushpull development test project

This project is a partially implemented web API that returns historical stock market data (open, close, high and low prices) for stocks in the [Indian Nifty50](https://www.nseindia.com/) stock index.

The project is implemented using python 3.9 and the [starlette](https://www.starlette.io/) ASGI web framework.

## Getting started
* Create virtual environment : `python -m venv .venv`
* Activate virtual environment : `.venv\Scripts\activate`
* Install requirements using `pip install -r requirements.txt`
* Run test cases: `pytest tests`
* Run test coverage: `pytest --cov nifty --cov-report term-missing`
* Run the server using `python -m nifty`
* Access the endpoint at `localhost:8888/nifty/stocks/{symbol}`

## Test cases:
#### 1) Return historical price data (GET /nifty/stocks/{symbol}/?year={year})

Implement the `price_data` function in `__main__.py` to return **open**, **close**, **high** and **low** prices for the requested symbol as JSON records. 
* [x] DONE - The data is loaded from the file `data/nifty50_all.csv` and saved in `data/nifty50_all.csv` at shutdown (look for startup and shutdown event in code)
* [x] DONE - The endpoint returns one record for each row of data in the file as List[StockPrices]. Test case `test_price_data` (all parameterized ones)
* [x] DONE - Returned data is sorted by date, most recent data first. Test case `test_price_data_sorted_by_date_desc`
* [x] DONE - If an invalid symbol is requested, the endpoint returns 400(BAD_REQUEST) with an appropriate error message. Test case `test_price_data` case 3
* [x] DONE - The solution allows the dataset to be updated (e.g. new data added) without restarting the app - Test case `test_add_price_data_and_check_count_of_record`

#### 2) Allow the price data to be filtered by year

* [x] DONE - Only returns rows for the specified year (and symbol). Testcase `test_price_data` case 4
* [x] DONE - When there is no data for the specified year, an empty list is returne. Testcase `test_price_data` case 5 
* [x] DONE - When year is invalid, the endpoint returns 400 and an appropriate error message. Testcase `test_price_data` case 6 


#### 3) Extend the endpoint to allow new data to be added

* [x] DONE - The endpoint only accepts (list of) JSON and allows prices for one or more days to be added to the dataset. Test case `test_add_price_data_multiple_and_check_count_of_record` covers multiple dates and `test_add_price_data_and_check_count_of_record` covers single date
* [x] DONE - It only allows new data to be added, it does not allows an existing value to be updated. Test case `test_add_price_data` case 8 covers that 
* [x] DONE - Any subset of **OPEN**, **CLOSE**, **HIGH**, **LOW** is accepted - no other price-types is accepted. Test case `test_add_price_data` case 7 covers that 
* [x] DONE - Updates are validated as follows:
  * [x] DONE - Dates only in the format DD/MM/YYYY. Test case `test_add_price_data` case 4
  * [x] DONE - Prices are within 1 standard deviation of the prior 50 values for that combination of symbol and price-type. Test case `test_add_price_data` case 2 
* [x] DONE - New data is persisted and is immediately accessible via GET. Test case `test_add_price_data_and_check_count_of_record` covers that

