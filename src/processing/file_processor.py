"""File processing pipeline: route uploaded files to SQL or ChromaDB."""

import csv
import io
import os
import sqlite3
import tempfile

from src.config.settings import get_sqlite_path

# Column definitions for each table.
# required: columns that must be present in the CSV
# all_cols: full ordered column list for INSERT
# auto_id: the auto-increment primary key column (excluded from CSV requirement)
TABLE_SCHEMAS = {
    "customers": {
        "required": {"name", "email"},
        "all_cols": [
            "customer_id",
            "name",
            "email",
            "phone",
            "account_type",
            "subscription_tier",
            "join_date",
            "address",
            "account_status",
        ],
        "auto_id": "customer_id",
    },
    "products": {
        "required": {"name", "category", "price"},
        "all_cols": [
            "product_id",
            "name",
            "category",
            "price",
            "description",
        ],
        "auto_id": "product_id",
    },
    "tickets": {
        "required": {"customer_id", "subject", "description"},
        "all_cols": [
            "ticket_id",
            "customer_id",
            "subject",
            "description",
            "category",
            "priority",
            "status",
            "channel",
            "assigned_agent",
            "created_at",
            "resolved_at",
            "resolution",
            "satisfaction_rating",
        ],
        "auto_id": "ticket_id",
    },
}


def detect_csv_table(headers):
    """Auto-detect which table a CSV maps to based on its column headers.

    Returns the table name or None if no match.
    """
    header_set = {h.strip().lower() for h in headers}

    best_match = None
    best_score = 0

    for table_name, schema in TABLE_SCHEMAS.items():
        # Check if all required columns are present
        required = {c.lower() for c in schema["required"]}
        if not required.issubset(header_set):
            continue

        # Score by how many of the table's columns match
        all_cols = {c.lower() for c in schema["all_cols"]}
        score = len(header_set & all_cols)
        if score > best_score:
            best_score = score
            best_match = table_name

    return best_match


def validate_csv_data(rows, table_name):
    """Validate CSV rows against a table schema.

    Returns (is_valid, errors) tuple.
    """
    schema = TABLE_SCHEMAS.get(table_name)
    if not schema:
        return False, [f"Unknown table: {table_name}"]

    errors = []
    required = schema["required"]

    for i, row in enumerate(rows):
        row_lower = {k.strip().lower(): v for k, v in row.items()}
        for col in required:
            val = row_lower.get(col.lower(), "").strip()
            if not val:
                errors.append(f"Row {i + 1}: missing required field '{col}'")

    # Type validation for numeric fields
    if table_name == "products":
        for i, row in enumerate(rows):
            row_lower = {k.strip().lower(): v for k, v in row.items()}
            price = row_lower.get("price", "").strip()
            if price:
                try:
                    float(price)
                except ValueError:
                    errors.append(
                        f"Row {i + 1}: 'price' must be numeric, got '{price}'"
                    )

    if table_name == "tickets":
        for i, row in enumerate(rows):
            row_lower = {k.strip().lower(): v for k, v in row.items()}
            cid = row_lower.get("customer_id", "").strip()
            if cid:
                try:
                    int(cid)
                except ValueError:
                    errors.append(
                        f"Row {i + 1}: 'customer_id' must be integer, got '{cid}'"
                    )

    return len(errors) == 0, errors


def insert_csv_to_sqlite(rows, table_name, db_path=None):
    """Insert CSV rows into a SQLite table with auto-ID assignment.

    Returns the number of rows inserted.
    """
    db_path = db_path or get_sqlite_path()
    schema = TABLE_SCHEMAS[table_name]
    auto_id = schema["auto_id"]
    all_cols = schema["all_cols"]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get current max ID
    cursor.execute(f"SELECT COALESCE(MAX({auto_id}), 0) FROM {table_name}")  # noqa: S608
    next_id = cursor.fetchone()[0] + 1

    inserted = 0
    for row in rows:
        # Normalize header keys to lowercase
        row_lower = {k.strip().lower(): v.strip() for k, v in row.items()}

        values = []
        for col in all_cols:
            if col == auto_id:
                values.append(next_id)
                next_id += 1
            else:
                values.append(row_lower.get(col.lower(), None) or None)

        placeholders = ", ".join(["?"] * len(all_cols))
        col_names = ", ".join(all_cols)
        cursor.execute(
            f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})",  # noqa: S608
            values,
        )
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


def _get_table_count(table_name, db_path=None):
    """Get current row count in a table."""
    db_path = db_path or get_sqlite_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")  # noqa: S608
    count = cursor.fetchone()[0]
    conn.close()
    return count


def _process_csv(uploaded_file, st):
    """Process a CSV file: detect table, validate, insert into SQLite."""
    content = uploaded_file.getvalue().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    headers = reader.fieldnames or []
    rows = list(reader)

    with st.status(f"Processing **{uploaded_file.name}**...", expanded=True) as status:
        st.write("Detecting file type... **CSV** (structured data)")

        st.write(f"Found **{len(rows)}** rows with columns: `{', '.join(headers)}`")

        table_name = detect_csv_table(headers)
        if not table_name:
            status.update(label=f"{uploaded_file.name} - Failed", state="error")
            st.error(f"Could not match columns to any known table. Headers: {headers}")
            return False

        st.write(f"Matched to table: **{table_name}**")

        is_valid, errors = validate_csv_data(rows, table_name)
        if not is_valid:
            status.update(
                label=f"{uploaded_file.name} - Validation failed", state="error"
            )
            for err in errors[:5]:
                st.error(err)
            return False
        st.write("Validating data... **Passed**")

        count_before = _get_table_count(table_name)
        st.write(f"Current table count: **{count_before}**")

        st.write(f"Inserting **{len(rows)}** records...")
        inserted = insert_csv_to_sqlite(rows, table_name)

        count_after = _get_table_count(table_name)
        status.update(
            label=f"{uploaded_file.name} - Done! ({table_name}: {count_before} -> {count_after}, +{inserted})",
            state="complete",
        )
    return True


def _process_pdf(uploaded_file, st):
    """Process a PDF file: save to temp, chunk, index into ChromaDB."""
    from src.db.vector_store import add_pdf_files, get_document_count

    with st.status(f"Processing **{uploaded_file.name}**...", expanded=True) as status:
        st.write("Detecting file type... **PDF** (unstructured document)")

        st.write("Saving file for processing...")
        temp_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.write("Chunking and indexing into vector store...")
        num_chunks = add_pdf_files([temp_path])

        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

        doc_count = get_document_count()
        status.update(
            label=f"{uploaded_file.name} - Done! Created {num_chunks} chunks (total: {doc_count})",
            state="complete",
        )
    return True


def _process_txt(uploaded_file, st):
    """Process a TXT file: save to temp, chunk, index into ChromaDB."""
    from src.db.vector_store import add_text_files, get_document_count

    with st.status(f"Processing **{uploaded_file.name}**...", expanded=True) as status:
        st.write("Detecting file type... **TXT** (unstructured document)")

        st.write("Saving file for processing...")
        temp_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.write("Chunking and indexing into vector store...")
        num_chunks = add_text_files([temp_path])

        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

        doc_count = get_document_count()
        status.update(
            label=f"{uploaded_file.name} - Done! Created {num_chunks} chunks (total: {doc_count})",
            state="complete",
        )
    return True


def process_uploaded_files(uploaded_files, st):
    """Main entry point: process a list of uploaded files.

    Routes each file to the appropriate handler based on extension.
    Returns (success_count, failure_count).
    """
    success = 0
    failure = 0

    for uploaded_file in uploaded_files:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        try:
            if ext == ".csv":
                ok = _process_csv(uploaded_file, st)
            elif ext == ".pdf":
                ok = _process_pdf(uploaded_file, st)
            elif ext == ".txt":
                ok = _process_txt(uploaded_file, st)
            else:
                st.warning(f"Unsupported file type: {uploaded_file.name}")
                failure += 1
                continue

            if ok:
                success += 1
            else:
                failure += 1
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {e}")
            failure += 1

    return success, failure
