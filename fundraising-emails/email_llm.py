import json
import time
import sys
import re
from sqlite_utils import Database
import llm

# Define schema for the expected output
schema = {
    "type": "object",
    "properties": {
        "committee": {
            "type": ["string", "null"],
            "description": "The name of the committee from the disclaimer (without 'Paid for by' prefix)"
        },
        "sender": {
            "type": ["string", "null"],
            "description": "The name of the person mentioned as the author of the email"
        }
    },
    "required": ["committee", "sender"]
}

def process_email(email, model):
    try:
        prompt = f"""Extract the following information from this email:
1. 'committee': The name of the committee in the disclaimer that begins with "Paid for by" but do not include the "Paid for by" text itself. If no committee is present, use null.
2. 'sender': The name of the person, if any, mentioned as the author of the email. If there is no person named, use null.

Email body:
{email['body']}"""
        
        response = model.prompt(
            prompt,
            schema=schema
        )
        
        # Parse the JSON response
        response_text = response.text()
        parsed_response = json.loads(response_text)
        time.sleep(0.3)
        return parsed_response | email
    except json.JSONDecodeError as e:
        print(f"    JSON decode error: {e}")
        return None
    except Exception as e:
        print(f"    Error processing email: {e}")
        return None

def retry_failures(failures_file, output_file):
    """
    Retry processing failed entries from a failures JSON file
    
    Args:
        failures_file (str): Path to the JSON file containing failed entries
        output_file (str): Path to save successful retries
    """
    print(f"Retrying entries from {failures_file}")
    
    try:
        with open(failures_file, 'r') as file:
            failures = json.load(file)
    except FileNotFoundError:
        print(f"No failures file found at {failures_file}")
        return
    
def main(year, month, name, model_name):
    db = Database('/Users/dwillis/code/ddhq_code/emails.db')
    entities = []
    failures = []
    
    # Derive model_file from model_name: convert to lowercase and replace hyphens/dots with underscores
    model_file = re.sub(r'[-.]', '_', model_name.lower())
    
    # Get the model
    model = llm.get_model(model_name)
    
    print(f"Processing emails for year={year}, month={month}")
    query = f"year = {year} and month = {month} and rowid != 46227 and disclaimer = 'TRUE'"
    print(f"Query: {query}")
    
    count = 0
    for email in db['emails'].rows_where(query, order_by='date', limit=1000):
        count += 1
        print(f"Processing email {count}: {email['subject']}")
        result = process_email(email, model)
        if result:
            entities.append(result)
            print("  ✓ Success")
        else:
            failures.append(email)
            print("  ✗ Failed")
    
    print(f"\nTotal emails processed: {count}")
    print(f"Successful: {len(entities)}")
    print(f"Failed: {len(failures)}")
    
    # Save initial results
    entities_file = f"{model_file}_{name}_{year}.json"
    failures_file = f"{model_file}_{name}_{year}_failures.json"
    
    print(f"\nSaving results to {entities_file}")
    with open(entities_file, 'w') as file:
        json.dump(entities, file, indent=4)
    
    print(f"Saving failures to {failures_file}")
    with open(failures_file, 'w') as file:
        json.dump(failures, file, indent=4)
    
    print("\nDone!")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python email_llm.py <model> <year> <month> <name>")
        print("Example: python email_llm.py claude-haiku-4.5 2024 11 november_2024")
        sys.exit(1)
    
    model_name = sys.argv[1]
    year = int(sys.argv[2])
    month = int(sys.argv[3])
    name = sys.argv[4]
    
    main(year, month, name, model_name)
