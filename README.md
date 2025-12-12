# DocSeek

## Project Overview

DocSeek is an intelligent document management system with RAG (Retrieval-Augmented Generation) capabilities, OCR processing and semantic search functionality.

## Key Features

- **Document Upload & Management**: Support for both native and scanned PDFs
- **GPU-Accelerated OCR**: DeepSeek-OCR integration for scanned documents via Lambda AI
- **Semantic Search**: ChromaDB-powered RAG for intelligent document retrieval
- **Role-Based Access Control**: Two user groups (Uploader & Searcher) with distinct permissions
- **Real-time Processing**: Celery-based asynchronous task processing

## Architecture

- **Backend**: Django, Python
- **Task Queue**: Celery + Redis
- **Database**: SQLite (dev) / PostgreSQL (production)
- **RAG**: ChromaDB + Sentence Transformers
- **OCR**: DeepSeek-OCR (GPU server via Lambda Cloud)
- **GPU API**: FastAPI (remote OCR processing)
- **Document Processing**: Docling
- **Frontend**: Bootstrap 5, HTML/CSS , JS

## Installation & Setup

### Local Setup

1. **Clone the repository**

```bash
git clone https://github.com/albanz27/DocSeek.git
cd DocSeek
```

2. **Create virtual environment**

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Run migrations**

```bash
python manage.py migrate
```

5. **Create superuser**

```bash
python manage.py createsuperuser
```

6. **Load pre-populated database**

```bash
# You cad use the db.sqlite3 that is included in the repo
# Otherwise, use the provided fixture:
python manage.py loaddata initial_data.json
```

### GPU Server Setup (for OCR functionality)

**IMPORTANT**: OCR functionality for scanned PDFs requires a remote GPU server. Follow these steps to set it up.

#### Step 1: Initialize GPU Server (Lambda Cloud)

Connect to the Lambda GPU instance and run the setup script:

```bash
ssh ubuntu@<IP_ADDRESS>
cd /lambda/nfs/docseek-ocr-storage/docseek
./setup_new_instance.sh
```

#### Step 2: Start OCR Server on GPU

Keep this terminal open while using the application:

```bash
./start_server.sh
```

This starts the FastAPI server with DeepSeek-VL model on the GPU.

#### Step 3: Create SSH Tunnel

On your **local machine**, create an SSH tunnel to forward GPU server requests:

```bash
ssh -N -L 8000:localhost:8000 ubuntu@<IP_ADDRESS>
```

---

### Running the Application

Now that the GPU server is ready, start all required services:

#### Terminal 3: Start Redis

```bash
docker-compose up
```

#### Terminal 4: Start Celery Worker

```bash
celery -A config worker -l info -Q celery,default,ocr --pool=solo
```

#### Terminal 5: Start Django Development Server

```bash
python manage.py runserver
```

---

## User Accounts (Pre-populated Database)

### Test Accounts

| Username    | Password    | Role     | Permissions                       |
| ----------- | ----------- | -------- | --------------------------------- |
| `uploader1` | `test1234`  | Uploader | Upload, manage, process documents |
| `searcher1` | `test1234`  | Searcher | Search & view all documents       |
| `admin`     | `admin1234` | Admin    | Full access                       |

---

## How to Use

### For Uploaders

1. **Login** with uploader account
2. **Upload Document**:
   - Navigate to "Uploader Dashboard"
   - Click "Upload New Document"
   - Select PDF type (Native or Scanned)
   - Upload file
3. **Process Document**:
   - Click "Process" on uploaded document
   - For scanned PDFs: OCR will run automatically
   - Wait for processing to complete
4. **Manage Documents**:
   - View processing status
   - Rename or delete documents

### For Searchers

1. **Login** with searcher account
2. **Semantic Search**:
   - Navigate to "Semantic Search"
   - Enter natural language query
   - View relevant passages from all documents
3. **View Documents**:
   - Click on any document to view PDF
   - Navigate to specific pages from search results

