# **PRD — Rev Exporter Tool (Corrected to Official Rev.com API Docs)**

**Purpose:** Create a repo/tool that configures Rev API credentials, connects to a Rev account, and downloads **all media files** and **all transcript-type deliverables** for every completed order.

---

# **1. Product Overview**

### **Name:** `rev-exporter`

### **Type:** CLI tool + importable client library

### **API Source:** Official Rev.com API ([https://www.rev.com/api/docs](https://www.rev.com/api/docs))

### **Primary Functionality**

1. Load and validate Rev API credentials.

2. Enumerate all orders through the paginated `/orders` endpoint.

3. Retrieve full order metadata via `/orders/{order_number}`.

4. For each order, iterate through all **attachments**.

5. Download attachment content (media + transcripts) through the official `/attachments/{id}/content{.ext}` endpoint.

6. Save files locally in structured folders.

---

# **2. Goals & Success Criteria**

### **Goals**

* Export all historical Rev media + transcripts.

* Support incremental syncing (idempotent).

* Safe to re-run with no duplicates.

* Simple configuration and clear logs.

### **Success**

* Running `rev-exporter sync` mirrors a user's entire Rev account locally.

* Works for thousands of orders with stable pagination and error handling.

---

# **3. Users & Use Cases**

### **Primary User**

* Developers or power users with Rev accounts needing local archives for analytics, research, or migration.

### **Use Cases**

* Full account backup.

* Pulling down transcripts for NLP analysis.

* Syncing new orders nightly via cron or an agent.

---

# **4. Scope**

### **In Scope (v1)**

* Auth config

* Order listing (pagination)

* Order detail retrieval

* Attachment metadata retrieval

* Attachment content download

* Local directory structure

* CLI interface

### **Out of Scope**

* Creating new orders

* Editing transcripts

* Uploading media

* Rev AI Notetaker / Workspaces integrations

---

# **5. High-Level System Workflow**

### **Step 1 — Load API keys**

* Accept via environment variables or config file:

  * `REV_CLIENT_API_KEY`

  * `REV_USER_API_KEY`

* Validate keys by performing a minimal `GET /api/v1/orders?page=0&results_per_page=1`.

---

### **Step 2 — List all orders**

Use official endpoint:

```
GET /api/v1/orders?page={page}&results_per_page={n}
```

**Notes from official docs:**

* Returns:

  * `total_count`

  * `results_per_page`

  * `page`

  * `orders: [ { order_number, status, placed_on, … } ]`

Pagination continues until `orders` array is empty.

---

### **Step 3 — Retrieve each order's details**

```
GET /api/v1/orders/{order_number}
```

**Official behavior:**

* Returns all order details.

* Includes an array of **attachments**:

  * Each item includes:

    * `id`

    * `name`

    * `type` (deliverable/media type)

    * `download_uri` (not always direct-download; may be informational)

    * other documented properties

(You do *not* assume extra fields like `kind` unless present in docs.)

---

### **Step 4 — For each attachment, retrieve metadata**

```
GET /api/v1/attachments/{attachment_id}
```

**Why:** Some metadata fields only appear at the attachment-level (e.g., deliverable type for transcripts vs. captions vs. media).

This endpoint provides the authoritative metadata for file type determination.

---

### **Step 5 — Download attachment content**

**Official endpoint:**

```
GET /api/v1/attachments/{attachment_id}/content
GET /api/v1/attachments/{attachment_id}/content.{extension}
```

**Format selection:**

* `.json`

* `.txt`

* `.docx`

* `.srt` (for captions)

* raw media (mp3/mp4/etc depending on the original upload)

**Accept headers may also be used**, per official docs.

This is the **only** supported method for downloading media + transcripts.

---

### **Step 6 — Store files locally**

Directory structure (v1):

```
<output_root>/
  <order_number>/
    attachments.json            # order metadata
    media/
      <attachment_id>_<name>.<ext>
    transcripts/
      <attachment_id>_<name>.<ext>
    other/
      <attachment_id>_<name>.<ext>
```

Tool maintains a local index of downloaded attachment IDs for idempotency.

---

# **6. Functional Requirements**

## **6.1 Auth**

* Tool must attach the official header:

```
Authorization: Rev CLIENT_API_KEY:USER_API_KEY
```

(as required by official documentation)

## **6.2 Order Enumeration**

* Must paginate until all results retrieved.

* Must respect parameters:

  * `page`

  * `results_per_page`

* Must capture:

  * `order_number`

  * `status`

  * `placed_on`

## **6.3 Order Filtering**

* Only **completed** orders should be downloaded.

* Official docs list status values; rely on those exactly as documented.

## **6.4 Attachment Processing**

* Must read attachments from `GET /orders/{order_number}`.

* Then refine details via `GET /attachments/{id}`.

* File classification uses only the fields Rev actually documents:

  * `type`

  * `name`

(Not invented fields like `kind`.)

## **6.5 Download Behavior**

* Use `GET /attachments/{id}/content{.ext}`.

* Allow user to specify preferred download formats:

  * transcripts: JSON or TXT

  * captions: SRT

  * fallback = server default format

## **6.6 CLI Requirements**

Provide commands:

### `rev-exporter test-connection`

* Performs minimal GET request to validate API keys.

### `rev-exporter sync`

* Lists all orders

* Filters completed ones

* Downloads all media + transcript attachments

* Skips already-downloaded items

### Flags:

* `--output-dir`

* `--since <ISO_DATE>`

* `--include-media / --no-include-media`

* `--include-transcripts / --no-include-transcripts`

* `--dry-run`

* `--debug`

---

# **7. Non-Functional Requirements**

### **Performance**

* Efficient pagination

* Optional concurrency for downloads

### **Reliability**

* Retries for network errors

* Graceful handling of missing attachments

### **Observability**

* Structured logs (INFO/WARN/ERROR)

* Final summary:

  * number of orders scanned

  * number of attachments downloaded

  * failures

### **Security**

* No logging of API keys

* ENV variable first, config file second

---

# **8. Official API Endpoints to Use (Final Verified List)**

All endpoints below are DIRECTLY documented on rev.com:

### **Authentication**

Uses header:

`Authorization: Rev CLIENT:USER`

(Required on every call)

---

### **Orders**

* **List orders**

  `GET /api/v1/orders?page={page}&results_per_page={n}`

  (Official: paginated, includes order summaries)

* **Get order details**

  `GET /api/v1/orders/{order_number}`

  (Official: includes attachments array)

---

### **Attachments**

* **Get attachment metadata**

  `GET /api/v1/attachments/{attachment_id}`

  (Official: metadata only)

* **Download attachment content**

  `GET /api/v1/attachments/{attachment_id}/content`

  `GET /api/v1/attachments/{attachment_id}/content.{extension}`

  (Official: returns actual file data)

* **Generate shareable link (optional)**

  `POST /api/v1/attachments/{attachment_id}/share`

---

