import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from collections import defaultdict
import json
import os
from prettytable import PrettyTable


# Google Sheets Setup
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS_INFO = json.loads(os.environ['creds'])  # Decodes the environment variable
SPREADSHEET_ID = "1jNF9dM8jqkJBCoWkHhPYtRDOtXTDtGt6Omdq5cZpX8U"  # Update with your Google Sheets ID
SHEET_NAME = "Foglio1"  # Name of the sheet

print("Welcome to the Task Logger Program!")

# Authorize and open the sheet
creds = Credentials.from_service_account_info(CREDS_INFO, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)


# Function to get the current date and time
def get_current_datetime():
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")  # Format: DD-MM-YYYY HH:MM:SS


# Function to ensure headers in the Google Sheet
def ensure_headers():
    headers = ["Name", "Task", "Date", "Hours", "Type", "Recorded At"]
    existing_data = sheet.get_all_records()

    # Check if headers are missing or don't match
    if not existing_data:  # If the sheet is empty
        sheet.append_row(headers)
        print("Headers added to Google Sheets.")
    elif list(existing_data[0].keys()) != headers:  # If headers don't match
        print("Warning: The headers in the sheet don't match expected format.")


# Call ensure_headers to make sure headers are in place
ensure_headers()


# Helper functions
def get_date():
    while True:
        date_input = input("Enter the date (DD-MM-YYYY) or press Enter to use today's date: ")

        if not date_input.strip():  # User pressed Enter
            return datetime.now().strftime("%d-%m-%Y")

        try:
            # Validate and format the custom date
            custom_date = datetime.strptime(date_input, "%d-%m-%Y")
            return custom_date.strftime("%d-%m-%Y")
        except ValueError:
            print("Invalid date format. Please use DD-MM-YYYY.")


def select_task_type():
    while True:
        print("\nSelect Task Type:")
        print("1. Administrative")
        print("2. Marketing")
        print("3. Product")
        type_choice = input("Enter the number corresponding to the task type: ")

        if type_choice == '1':
            return "Administrative"
        elif type_choice == '2':
            return "Marketing"
        elif type_choice == '3':
            return "Product"
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


# Function to log a new task entry
def log_task():
    name = input("Enter your name: ")
    task = input("Enter the task: ")
    date = get_date()  # Function to get date (custom or current)
    hours = float(input("Enter hours worked: "))
    task_type = select_task_type()  # Function to select the task type
    recorded_at = get_current_datetime()  # Get the current date and time

    # Append data to the Google Sheet
    try:
        sheet.append_row([name, task, date, hours, task_type, recorded_at])
        print("Task logged successfully.")
    except Exception as e:
        print(f"Error logging task: {e}")


# Function to display all logged tasks
def view_logs():
    try:
        print("\nView Logs in Terminal:")

        records = sheet.get_all_records()
        if not records:
            print("No logs available to view.")
            return

        table = PrettyTable()
        table.field_names = records[0].keys()
        for record in records:
            table.add_row(record.values())
        print(table)

    except Exception as e:
        print(f"Error viewing logs: {e}")


# Helper function to filter tasks by the selected month
def filter_tasks_by_month(records):
    from datetime import datetime
    import calendar

    today = datetime.now()

    months = []
    for i in range(12):
        month = (today.month - i - 1) % 12 + 1  # Handle month rollover
        year = today.year if today.month - i > 0 else today.year - 1
        months.append((calendar.month_name[month], month, year))

    months = months[::-1]

    print("\nFilter by Month:")
    for idx, (month_name, _, _) in enumerate(months, start=1):
        print(f"{idx}. {month_name}")

    try:
        choice = int(input("Enter the number corresponding to your choice: ")) - 1
        if choice < 0 or choice >= len(months):
            print("Invalid choice.")
            return [], None
    except ValueError:
        print("Invalid input. Please enter a number.")
        return [], None

    selected_month_name, selected_month, selected_year = months[choice]
    filtered_records = [
        record for record in records
        if datetime.strptime(record['Date'], "%d-%m-%Y").month == selected_month and
           datetime.strptime(record['Date'], "%d-%m-%Y").year == selected_year
    ]

    return filtered_records, selected_month_name


# Function to display statistics in table format
def display_statistics_table():
    try:
        records = sheet.get_all_records()

        if not records:
            print("No logs found. Please log a task first.")
            return

        filtered_records, selected_month_name = filter_tasks_by_month(records)

        if not filtered_records:
            print(f"No records found for {selected_month_name}.")
            return

        task_type_data = defaultdict(float)
        collaborator_data = defaultdict(float)
        monthly_data = defaultdict(float)

        for record in records:
            date = datetime.strptime(record["Date"], "%d-%m-%Y")
            month_name = date.strftime("%B %Y")
            monthly_data[month_name] += float(record["Hours"])

        # Calculate task type and collaborator hours for the selected month
        selected_month_total_hours = 0  # Variable to track the total hours of the selected month

        for record in filtered_records:
            task_type_data[record['Type']] += float(record['Hours'])
            collaborator_data[record['Name']] += float(record['Hours'])
            selected_month_total_hours += float(record["Hours"])  # Add hours to the total for selected month

        def generate_table(data, title, headers):
            table = PrettyTable()
            table.title = title
            table.field_names = headers
            for key, value in data.items():
                table.add_row([key, f"{value:.2f}h"])
            print(table)

        generate_table(task_type_data, f"Hours per Task Type for {selected_month_name}", ["Task Type", "Hours"])
        generate_table(collaborator_data, f"Hours by Collaborator for {selected_month_name}", ["Collaborator", "Hours"])
        print(f"\nTotal Hours for {selected_month_name}: {selected_month_total_hours:.2f}h")

    except Exception as e:
        print(f"Error displaying statistics: {e}")


# Main function to display the menu and execute chosen options
def main():
    while True:
        print("\nOptions:")
        print("1. Log Task")
        print("2. View Logs")
        print("3. View Statistics")
        print("4. Exit")

        choice = input("Choose an option: ")
        if choice == '1':
            log_task()
        elif choice == '2':
            view_logs()
        elif choice == '3':
            display_statistics_table()
        elif choice == '4':
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
