# Fivetran Guesty Custom Connector

A custom Fivetran Connector built using the **Fivetran Connector SDK** to incrementally extract reservation data from the **Guesty Open API** (v1) and load it into your destination data warehouse.

## Features

- **OAuth 2.0 Authentication**: Automatically requests and caches access tokens using Client Credentials.
- **Incremental Syncing**: Tracks the `lastUpdatedAt` timestamp to sync only new or updated reservations.
- **Automatic Pagination**: Fetches records in batches of 100 using API offsets.
- **Rate Limit Handling**: Listens for HTTP `429 Too Many Requests` responses and backs off automatically.
- **State Management**: Saves state checkpoints using Fivetran's `op.checkpoint` mechanism.

## Data Schema

The connector syncs data into the `guesty_reservations` table using `id` as the primary key.

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `id` | String (Primary Key) | Guesty internal reservation ID (`_id`) |
| `account_id` | String | Guesty Account ID |
| `listing_id` | String | Associated Listing ID |
| `listing_title` | String | Title of the listing |
| `unit_name` | String | Assigned unit title |
| `status` | String | Reservation status (e.g., `confirmed`, `canceled`) |
| `confirmation_code` | String | Booking confirmation code |
| `check_in` | String (ISO8601) | Check-in date/time |
| `check_out` | String (ISO8601) | Check-out date/time |
| `source` | String | Booking source |
| `platform` | String | Integration platform (e.g., Airbnb, Booking.com) |
| `guest_id` | String | Guesty Guest ID |
| `guest_name` | String | Full name of the guest |
| `total_price` | Float | Total reservation price |
| `total_paid` | Float | Total amount paid |
| `balance_due` | Float | Remaining balance |
| `currency` | String | Currency code (e.g., USD, EUR) |
| `created_at` | String (ISO8601) | Reservation creation timestamp |
| `updated_at` | String (ISO8601) | Reservation last update timestamp |
| `imported_at` | String (ISO8601) | Timestamp when imported into Guesty |

## Setup & Configuration

### Prerequisites
- Python 3.9+
- Fivetran Connector SDK (`pip install fivetran-connector-sdk`)
- Guesty Open API Credentials (`client_id` and `client_secret`)

### Configuration JSON (`configuration.json`)
To run or deploy this connector, create a configuration JSON file with the following structure:

```json
{
  "client_id": "YOUR_GUESTY_CLIENT_ID",
  "client_secret": "YOUR_GUESTY_CLIENT_SECRET",
  "start_date": "2024-01-01T00:00:00.000Z"
}
