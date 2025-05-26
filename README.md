# RAG-BACK
Backend implementation for a Retrieval-Augmented Generation (RAG) system. It integrates document processing, embedding, storage, and querying functionalities.
## ⛓️‍💥 Live Links
UI - https://rag-frontend-ruddy.vercel.app/  
Swagger UI - https://73kls1ka81.execute-api.us-east-1.amazonaws.com/docs/

## 📸 Screenshots UI/ Swagger
<img width="240" alt="Screenshot 2025-05-26 at 10 55 27 PM" src="https://github.com/user-attachments/assets/a2963bd0-76c6-4d58-825b-ce1f4b39d6c3" />_
<img width="240" alt="Screenshot 2025-05-27 at 1 20 02 AM" src="https://github.com/user-attachments/assets/74457476-2ac8-4dd1-9b9d-d360e5992280" />_
<img width="240" alt="Screenshot 2025-05-27 at 1 43 22 AM" src="https://github.com/user-attachments/assets/1662265b-cce2-4c23-b47e-d18cc920dd84" />_
<img width="240" alt="Screenshot 2025-05-27 at 1 56 22 AM" src="https://github.com/user-attachments/assets/441f1883-1848-4041-a81f-d04956b1f311" />_

1. **File Upload Section:** Users can upload various document files. We have the option to select structured json to store non vector data for calculating aggregates
This enables the system to later compute aggregates like totals, averages, or counts from that structured data.
2. **Document Search & Q&A Section:** Allows users to search for previously uploaded documents by email. Once a document is selected, users can ask natural language questions about the document content. The system processes the query contextually based on the selected document.
3. **Aggregate Calculation Section:** If you searched for a JSON file marked as "Structured JSON", this section becomes available for selected json. Users can select fields and aggregation functions (like sum, average, min, max) to compute insights from the structured data.
4. **Swagger UI Integration:** Provides an interactive API documentation and testing interface. Developers and users can view, test, and interact with all available API endpoints directly from the browser.


## 🔧 Key Features
- FastAPI: Serves as the web framework for building RESTful APIs.
- OpenAI Embeddings: Utilizes OpenAI's models to generate vector representations of documents.
- Weaviate Vector Search: Employs Weaviate as the vector database for storing and retrieving document embeddings.


## 📁 Project Structure

* **app/:** Contains the main application code, including API endpoints and background workers.

  * **services/:** Embedding, parsing, and text chunking code.
  * **core/:** Contains database, schema validation code, and configs.
  * **main.py:** All APIs and routes; acts as the entry point for the API server.
  * **worker.py:** Entry point for the document parsing and embedding service for Lambda.
* **migrations/:** Relational database migration files.
* **Dockerfile.api:** Defines the Docker image for the API service (production).
* **Dockerfile.worker:** Defines the Docker image for the background worker service (production).
* **Dockerfile.dev:** Defines the Docker image for development (API service and document processing).
* **requirements.txt:** Lists the Python dependencies required for the project.
* **.pre-commit-config.yaml:** Configuration for pre-commit hooks to maintain code quality.

## ⚙️ Setup and Deployment

**Prerequisites:**

* Python 3.12
* Docker (for development)
* Direnv (if not using Docker)
* PostgreSQL
* Tesseract for OCR
* Weaviate account with a configured database
* Hosted PostgreSQL URL
* OpenAI developer account

### 🔨 Development:

**Docker**

* Build the Docker image:

```
docker build -t rag-server-dev -f Dockerfile.dev .
```

* Run the Docker container:

```
docker run -p 8000:8000 --env-file .env rag-server-dev
```

*Note: Refer to the environment setup to fill the .env file; otherwise, it will throw an error.*

**Direnv**

* Create `.envrc.local` and place all the environment variables inside.
* Run `direnv allow` to load them.
* Install Poetry and the required packages:

```
pip install poetry
poetry install
```

* Run migrations:

```
alembic upgrade head
```

* Run the server:

```
uvicorn app.main:app --port 8090 --reload
```

### 🎬 Production

Production deployment is configured on AWS with GitHub Actions for CI/CD.

**AWS Setup**

* Create ECR repositories for storing Docker images used for Lambda deployment:

  * `rag-api-server` for the FastAPI server.
  * `rag-worker` for the document parser and embedding.
  * *(Optional)* `tesseract-ocr` for packaging OCR within `rag-worker`.
* Create an SQS Standard queue; add its URL to the environment variable.
* Create two Lambda functions:

  * One for the worker (parsing and embedding documents).
  * One for the API.
* Create IAM roles:

  * **API Server Lambda:**

    * Lambda Invoke
    * S3 GET, PUT, LIST for the configured bucket
    * SQS full access
  * **Worker Lambda:**

    * S3 GET, LIST for the bucket
    * SQS full access
  * Add environment variables to both Lambdas as per the environment setup section.
* Create an API Gateway (HTTP v2 protocol) linked to the API Lambda.
* Create an AWS user for GitHub Actions, and add `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, and `AWS_ACCOUNT_ID` to the repo secrets.

**Database Setup (Relational SQL)**
- Setup database on neondb or aws and copy the url and add it to env variable `PROD_DATABASE_URL`
- Run migration from local terminal whenever there is any new changes in the database
```
    alembic upgrade head
```

**Weaviate Vector Database setup**
- Create a cluster with dimensions set as 1538
- Collect API key and URL and store it in `WEAVIATE_OPENAI_ADMIN_KEY` and `WEAVIATE_URL` locally
- Then create a schema by running below command from backend directory
```
    python -m app.services.utils.create_schema_wrapper
```
**One time setup:**
- Build and push tesseract-ocr image to aws ecr repo which we created earlier and make sure its name matches in dockerfile.tesseract, use Dockerfile.tesseract for building image
    ```
        # Link aws account is connected with docker
        aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <accountid>.dkr.ecr.us-east-1.amazonaws.com
        # Build tesseract image
        docker build --platform linux/amd64 TESSERACT_image <accountid>.dkr.ecr.us-east-1.amazonaws.com/tesseract-ocr-aws:latest  -t tesseract-ocr-aws -f Dockerfile.tesseract .
        # Tag it
        docker tag tesseract-ocr-aws:latest <accountid>.dkr.ecr.us-east-1.amazonaws.com/tesseract-ocr-aws:latest

        # Push to ecr
        docker push <accountid>.dkr.ecr.us-east-1.amazonaws.com/tesseract-ocr-aws:latest
    ```
- Make sure to update github workflow `deploy_api.yml` to use Dockerfile.worker.tesseract if ocr is needed else use Dockerfile.worker
- Now if you trigger Github actions it should automatically deploy the code to lambdas. Secrets need to filled

**Note:**

* Check logs for permission-related errors and adjust as needed.
* Lambda names for the worker and API are hardcoded as `rag-worker` and `rag-api-server`. Ensure your Lambda names match.

## 🕵🏻‍♂️ Env & Secrets

#### Environment Variables:

* `WEAVIATE_OPENAI_ADMIN_KEY` – Weaviate key for OpenAI-based vector embedding
* `WEAVIATE_URL` – Weaviate database URL
* `OPENAI_API_KEY` – OpenAI key
* `PROD_DATABASE_URL` – PostgreSQL URL
* `BUCKET_NAME` – S3 bucket for uploaded files
* `SQS_QUEUE_URL` – SQS URL
* `DEVELOPMENT` – Disable S3 calls and process files locally in dev

#### GitHub Actions Secrets:

* `AWS_ACCESS_KEY_ID`
* `AWS_ACCOUNT_ID`
* `AWS_REGION`
* `AWS_SECRET_ACCESS_KEY`
* `TESSERACT_IMAGE`

## 🏛️ ⚙️ Architecture & Detailed Workflow
![Diagram](./ArchitectureDiagram.png)
### 📥 1. Document Upload & Task Creation
- User sends a POST /upload-document request with:
    - Document file (PDF, DOCX, TXT, or JSON)
    - User email
- The backend:
    - Stores the file either locally (in development) or uploads it to S3 (in production)
    - Creates a processing task entry in the TaskStatus table via SQLAlchemy
    - In development:
        - Calls directly calls process_document() for chunking, embedding and storing vectors in weaviate database
    - In production:
        - Sends a message to an AWS SQS queue for asynchronous background processing.
        - This queue trigger worker lambda which runs process_document() and freeing up the api server

### 📝 2. Document Ingestion & Embedding Generation
- The process_document(task_id) function:
    - Reads the file content
    - Splits the document into manageable chunks
    - Generates text embeddings for each chunk using an Open AI embedding model
    - Pushes each chunk embedding along with metadata (document name, text, chunk id) to the Weaviate vector database
    - Updates the task status to completed in the TaskStatus table

### 📡 3. Question-Answer Retrieval
- User sends a POST /document/query request with:
    - task_id
    - question
- The backend:
    - Retrieves the associated document task using the task_id
    - Generates an embedding for the user’s question
    - Queries Weaviate using a nearest neighbor vector search (near_vector) with:
        - A filter on the document’s file path to restrict to the specific document
        - The question embedding
    - Retrieves the top N relevant text snippets (e.g., top 3)
    - Returns these snippets in the API response

### 🗂️ Data Storage & Components
- PostgreSQL / SQLite (via SQLAlchemy ORM):
    - TaskStatus table tracks document uploads, processing status, and metadata.
- Weaviate:
    - Stores document chunk embeddings along with associated metadata.
    - Provides efficient vector similarity search via the near_vector query.
- AWS S3 (Production):
    - Stores uploaded documents in cloud storage.
- AWS SQS (Production):
    - Queues processing tasks for asynchronous background document processing.

### {} JSON Data RAG Extension (Bonus)
- Ingests structured JSON records into a separate JsonDataRecord collection
- Supports property-based aggregate queries like:
- Max/min/sum/avg on numerical fields


## 📖 API Documentation
### Base URL
https://73kls1ka81.execute-api.us-east-1.amazonaws.com/

### 📊 GET /health
- **Description:** Checks if the Weaviate client is ready.
- **Response:**
    ```
    {
        "weaviate": true
    }
    ```

### 📥 POST /upload-document
- **Description:** Uploads a new document to the system, generates embeddings, and indexes them into Weaviate.
- **Request:**
    - Content-Type: multipart/form-data
    - Form Data:
        - file (required) — The document file (PDF, DOCX, TXT, JSON)
- **Response:**
    ```
        {
            "message": "Document uploaded and processed successfully",
            "document_id": "abc123"
        }
    ```

### 📤 POST /document/query
- **Description:** Submit a query against a specific document, and retrieve the most relevant text snippets.

- **Request:**
    - Content-Type: application/json
    - Body:
        ```
        {
            "document_id": "abc123",
            "question": "What is the whistleblower policy?"
        }
        ```
- **Response:**
    - Task Present:
        ```
            {
                "answer": "The company encourages whistleblowing and ensures anonymity...",
                "metadata": {
                    "document_id": "abc123",
                    "text_snippet": "The company encourages whistleblowing and ensures anonymity for the whistleblower..."
                }
            }
        ```
    - Task id does not exist:
        ```
        {
           "error": "Task not found"
        }
        ```

### 📊 GET /task-status/{task_id}
- **Description:** Checks the processing status of a document.
- **Path Parameter:** task_id (required)
- **Response:**
    - Task Found
        ```
        {
            "task_id": "abc123",
            "status": "completed"
        }
        ```
    - Task Not Found
        ```
        {
            "error": "Task not found"
        }
        ```

### 📋 GET /users/tasks/{user_email}
- **Description:** Fetches all document processing tasks associated with a specific user.
- **Path Parameter:** user_email (required)
- **Response**:
    ```
    [
        {
            "task_id": 1,
            "user_email": "test@example.com",
            "error_message": null,
            "completed_at": null,
            "file_path": null,
            "file_name": "whistleblower-policy-ba-revised.pdf",
            "status": "completed",
            "created_at": "2025-05-24T19:55:20.597820"
        },
        ...
    ]
    ```



### POST /users/task/json-aggregator
- **Description:** Get Aggregator values for structured json data.
- **Path Parameter:**
    - task_id (required) : Document task id
    - field (required) : Numeric field which needs to be aggregated
- **Response**:
    ```
    {
    "task_id": "10",
    "field": "age",
    "output": {
        "count": 50,
        "maximum": 64,
        "minimum": 18,
        "mean": 44.32,
        "total": 2216
    }
    }
    ```
### 📊 API Docs URL (Auto-Generated)
The application exposes several API endpoints for document processing and querying. The API documentation is available via Swagger UI at:

https://73kls1ka81.execute-api.us-east-1.amazonaws.com/docs


## 📐 Design Choices
#### ⚙️ FastAPI for Backend API
Why:
- Lightweight, fast, and easy to use.
- Automatic OpenAPI documentation (/docs).
- Async-friendly for scalable request handling.

#### ☁️ AWS Lambda + S3 + SQS for Production
Why:
- Easy deployment on s3 no need of managing servers
- S3 offers scalable, durable storage for uploaded documents.
- SQS decouples ingestion requests from processing jobs for better scalability in production.
Trade-off:
- Initial API call take some time to load.
- Added setup complexity for queue management and cloud permissions.
- In development mode, tasks are processed synchronously for simplicity.
- Lambda deployment is Not good for processing big document files

#### 💾 PostgreSQL (via SQLAlchemy) for Task Tracking
Why:
- Reliable relational database for managing task status, metadata.
- Future Extensibility for user auth and analytics.

### 😥 Challenges
- Handling duplicate document uploads: For this implemented task lookup by file path + user_email to update existing records and delete and recreate weaviate object.
- Asynchronous processing in production: Decided on AWS SQS for task queuing, keeping local dev synchronous.
- Adding Tesseract to AWS Lambda was a pain: Packaging native binaries, managing shared library dependencies, and configuring TESSDATA_PREFIX correctly made the setup fragile and time-consuming.

### 🚀 Enhancement Plan
As the system scales and to maintain reliability under high concurrency, we should introduce the following improvements:
#### Retry Logic for OpenAI API:
- OpenAI accounts are subject to requests per minute (RPM) and tokens per minute (TPM) quotas. Exceeding these limits results in 429 Too Many Requests errors.
**Solution:**
Implement exponential backoff with jitter in the Worker Lambda when calling the OpenAI API.

#### User Rate Limiting
An unrestricted number of document uploads per user could flood the system, leading to API rate limit hits and degraded experience for other users.
**Solution:**
Introduce a user-level rate limit (e.g., 5 documents per minute)

#### PDF OCR is English Only
Currently, Tesseract PDF OCR functionality is limited to English-language documents. Multi-language support can be added by integrating libraries or using multilingual OCR services.

#### OCR is Slow and Doesn’t Support Long Documents
The current worker Lambda handles both OCR and embedding. Running OCR (via Tesseract) on a 4–5 page document takes around 30–40 seconds by lambda, which slows down the overall processing pipeline. For longer documents, this time increases significantly, making it inefficient and prone to timeouts.

**Solution:**
We can replace Tesseract with AWS Textract, which supports asynchronous processing via SNS notifications. This allows us to:
- Subscribe to Textract job completions via SNS
- Decouple OCR parsing and embedding into separate Lambdas
- Improve performance and scalability for documents requiring OCR.

#### In-House Embedding Model as Fallback
If OpenAI API quotas are exhausted, embedding generation halts — causing delays in document ingestion.
**Solution:**
- Host an in-house embedding model (e.g., sentence-transformers on Fargate)
- Use it as a fallback option when OpenAI is unavailable or limits are hit.
- Since local embeddings might differ in quality, maintain a separate Weaviate collection (e.g., LocalDocumentChunk) to avoid polluting OpenAI-embedded data.

#### 🗑️ Integrate Cleaning
Cleaning up files older than specific days can speed up fetch problems in future by reducing clutter and potential conflicts.
