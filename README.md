# linkedhelper_into_hubspot

## Summary
This application synchronizes contact data exported from LinkedHelper2 (CSV format) into HubSpot CRM. It automates the process of searching, deduplicating, merging, and updating HubSpot contacts based on advanced mapping and business rules. The script supports batch processing, robust error handling, and conditional debug output.

## Business Rules & Logic

### Contact Identification & Deduplication
- Searches for existing HubSpot contacts by email, LinkedIn user ID, hash ID, public ID, and name (with organization corroboration).
- Merges duplicate contacts, keeping the highest HubSpot ID as primary.

### Property Mapping & Update Logic
- Only updates properties if the new value differs from the existing value in HubSpot.
- Maps CSV fields to HubSpot properties, including custom logic for phone types, education, location, badges, and organization URLs.
- Normalizes organization website URLs and LinkedIn URLs (including transforming sales/people URLs to /in URLs and trimming after commas).

### Email Handling
- Extracts all email addresses from the record.
- Sets the first email as primary and adds others as secondary using legacy HubSpot endpoints.
- Ensures no trailing commas and filters out invalid emails.

### LinkedIn URL Logic
- If the LinkedIn URL is empty or a Sales Manager URL, replaces it with a normalized /in URL from the profile URL, trimming after the first comma.

### Batch Processing
- Supports processing a specified number of records starting from a given record number.

### Error Handling & Debug Output
- Logs failed record IDs and HTTP errors for diagnostics.
- Debug output is gated by a `DEBUG` flag at the top of the script.

### Other Business Rules
- Maps language labels to HubSpot language codes.
- Handles badges and boolean fields with flexible value normalization.
- Splits location into city, state, and country, with special handling for US states.

---

## Getting Started

### Required Environment Variables
- `HUBSPOT_API_KEY`: Your HubSpot private app access token. Set this in your environment before running the script.
  - On Windows PowerShell:
    ```powershell
    $env:HUBSPOT_API_KEY = "your-hubspot-api-key"
    ```

### Running the Batch Process
To start the batch process, run the following command from your project directory:

```powershell
python read_record.py <csv_file> <record_number> [num_records]
```

- `<csv_file>`: Path to your LinkedHelper2 CSV export file (e.g., `LinkedHelperData.csv`).
- `<record_number>`: The starting record number (1-based index).
- `[num_records]`: (Optional) Number of records to process in this batch. If omitted, processes all records from the starting point.

Example:
```powershell
python read_record.py LinkedHelperData.csv 1 100
```
This processes the first 100 records in the CSV file.

---
For more details, see the code and comments in `read_record.py`.
