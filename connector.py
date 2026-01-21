import requests
import time
import json
from typing import Dict

from fivetran_connector_sdk import Connector
from fivetran_connector_sdk import Logging as log
from fivetran_connector_sdk import Operations as op

__GUESTY_BASE_URL = "https://open-api.guesty.com/v1"
__AUTH_URL = "https://open-api.guesty.com/oauth2/token"
__RESERVATIONS_ENDPOINT = "/reservations"

def get_access_token(configuration: Dict) -> str:
    log.info("--- REQUESTING NEW TOKEN FROM GUESTY ---")
    payload = {
        'grant_type': 'client_credentials',
        'scope': 'open-api',
        'client_id': configuration.get("client_id"),
        'client_secret': configuration.get("client_secret")
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    response = requests.post(__AUTH_URL, data=payload, headers=headers)
    if response.status_code != 200:
        log.severe(f"Auth failed: {response.text}")
        response.raise_for_status()
    
    return response.json().get("access_token")

def fetch_reservations(configuration: Dict, state: Dict):
    current_time = time.time()
    token = state.get("access_token")
    token_time = state.get("token_generated_at", 0)

    if token and (current_time - token_time) < 72000:
        log.info(f"Using cached token. Age: {int(current_time - token_time)}s")
    else:
        token = get_access_token(configuration)
        state["access_token"] = token
        state["token_generated_at"] = current_time

    url = f"{__GUESTY_BASE_URL}{__RESERVATIONS_ENDPOINT}"
    since = state.get("last_updated") or configuration.get("start_date", "2024-01-01T00:00:00.000Z")
    
    all_fields = [
        "_id", "integration", "accountId", "guestId", "listingId", 
        "listing", "unit", "checkIn", "checkOut", "guest", "confirmationCode",
        "createdAt", "lastUpdatedAt", "status", "source", "importedAt",
        "money.totalPrice", "money.currency", "money.hostPayout", 
        "money.totalPaid", "money.balanceDue", "money.payments"
    ]
    fields_param = " ".join(all_fields)

    current_skip = 0
    new_last_updated = since

    while True:
        filters = [{"operator": "$gt", "field": "lastUpdatedAt", "value": since}]
        
        params = {
            "limit": 100,
            "skip": current_skip,
            "sort": "lastUpdatedAt",
            "fields": fields_param,
            "filters": json.dumps(filters)
        }
        
        headers = {'Authorization': f'Bearer {token}', 'accept': 'application/json'}
        
        log.info(f"Requesting Guesty reservations: skip {current_skip}, since {since}")
        res = requests.get(url, headers=headers, params=params)
        
        if res.status_code == 429:
            log.warning("Rate limit hit. Sleeping 60s...")
            time.sleep(60)
            continue
            
        res.raise_for_status()
        data = res.json()
        items = data.get("results", [])
        
        if not items:
            break

        for item in items:

            res_data = {
                "id": item.get("_id"),
                "account_id": item.get("accountId"),
                "listing_id": item.get("listingId"),
                "listing_title": item.get("listing", {}).get("title"),
                "unit_name": item.get("unit", {}).get("title"), 
                "status": item.get("status"),
                "confirmation_code": item.get("confirmationCode"),
                "check_in": item.get("checkIn"),
                "check_out": item.get("checkOut"),
                "source": item.get("source"),
                "platform": item.get("integration", {}).get("platform"),
                "guest_id": item.get("guestId"),
                "guest_name": item.get("guest", {}).get("fullName"),
                "total_price": item.get("money", {}).get("totalPrice"),
                "total_paid": item.get("money", {}).get("totalPaid"),
                "balance_due": item.get("money", {}).get("balanceDue"),
                "currency": item.get("money", {}).get("currency"),
                "created_at": item.get("createdAt"),
                "updated_at": item.get("lastUpdatedAt"),
                "imported_at": item.get("importedAt")
            }
            
            op.upsert(table="guesty_reservations", data=res_data)
            
            current_item_updated = item.get("lastUpdatedAt")
            if current_item_updated and current_item_updated > new_last_updated:
                new_last_updated = current_item_updated

        if len(items) < 100:
            break
        current_skip += 100

    state["last_updated"] = new_last_updated

def schema(configuration: dict):
    return [{"table": "guesty_reservations", "primary_key": ["id"]}]

def update(configuration: dict, state: dict):
    log.info("Starting Sync Cycle.")
    try:
        fetch_reservations(configuration, state)
    finally:
        op.checkpoint(state)
    log.info("Sync Cycle completed.")

connector = Connector(update=update, schema=schema)

if __name__ == "__main__":
    connector.debug()