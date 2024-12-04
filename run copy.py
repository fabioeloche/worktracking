import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from collections import defaultdict
import json
import html
import webbrowser
import os


# Google Sheets Setup
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS_INFO = json.loads(os.environ['creds'])  # Decodifica la variabile d'ambiente JSON
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

# Define helper functions
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
        records = sheet.get_all_records()
        if records:
            print("\nLogged Tasks:")
            for record in records:
                print(record)
        else:
            print("No logs found. Please log a task first.")
    except Exception as e:
        print(f"Error displaying logs: {e}")

# Helper function to filter tasks by the selected month
# Helper function to filter tasks by the selected month
def filter_tasks_by_month(records):
    from datetime import datetime
    import calendar

    # Get today's date
    today = datetime.now()

    # Generate the last 12 months including the current month
    months = []
    for i in range(12):
        month = (today.month - i - 1) % 12 + 1  # Correctly handle month rollover
        year = today.year if today.month - i > 0 else today.year - 1
        months.append((calendar.month_name[month], month, year))

    # Reverse the order to display months from earliest to latest
    months = months[::-1]

    # Display the filter options to the user
    print("\nFilter by Month:")
    for idx, (month_name, _, _) in enumerate(months, start=1):
        print(f"{idx}. {month_name}")

    # Get user selection
    try:
        choice = int(input("Enter the number corresponding to your choice: ")) - 1
        if choice < 0 or choice >= len(months):
            print("Invalid choice.")
            return [], None
    except ValueError:
        print("Invalid input. Please enter a number.")
        return [], None

    # Get selected month and year
    selected_month_name, selected_month, selected_year = months[choice]

    # Filter records based on the selected month and year
    filtered_records = []
    for record in records:
        try:
            task_date = datetime.strptime(record['Date'], "%d-%m-%Y")
            if task_date.month == selected_month and task_date.year == selected_year:
                filtered_records.append(record)
        except ValueError:
            print(f"Invalid date format in record: {record}")

    return filtered_records, selected_month_name


# Function to export filtered data to an HTML report
def export_html():
    try:
        # Fetch records from the Google Sheet
        records = sheet.get_all_records()

        if not records:
            print("No logs found. Please log a task first.")
            return

        # Filter tasks by the selected month
        filtered_records, selected_month_name = filter_tasks_by_month(records)

        if not filtered_records:
            print(f"No records found for {selected_month_name}.")
            return

        # Aggregate data for charts
        
        aggregated_data = defaultdict(float)
        task_type_data = defaultdict(float)
        for record in filtered_records:
            aggregated_data[record['Name']] += float(record['Hours'])
            task_type_data[record['Type']] += float(record['Hours'])

        # Prepare chart data




        names = json.dumps(list(aggregated_data.keys()))
        collaborator_names = list(aggregated_data.keys())  # List for dropdown
        hours = json.dumps([int(round(value)) for value in aggregated_data.values()])  # Rounded to integers
        total_hours = sum(task_type_data.values())
        task_types = list(task_type_data.keys())
        task_hours = [round((value / total_hours) * 100, 2) for value in task_type_data.values()]
        task_types_json = json.dumps(task_types)
        task_hours_json = json.dumps(task_hours)
        
        # Generate the HTML content
        html_data = f"""
        <html>
        <head>
            <title>Task Report - {selected_month_name}</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels"></script>
            <style>
                body {{
                    font-family: Arial, sans-serif; 
                    background-color: #f9f9f9; 
                    margin: 20px;
                    color: #333;
                }}
                h1, h2 {{
                    text-align: center;
                    font-weight: bold;
                }}
                .dropdown {{
                    display: flex;
                    justify-content: center;
                    margin: 10px 0;
                }}
                .dropdown select {{
                    font-size: 16px;
                    padding: 5px;
                }}
                .chart-container {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    margin: 20px 0;
                }}
                .chart {{
                    width: 50%;
                    margin: 20px;
                }}
                .table-container {{
                    margin: 20px auto;
                    width: 80%;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
                }}
                th, td {{
                    padding: 12px 15px;
                    text-align: left;
                    border: 1px solid #ddd;
                }}
                th {{
                    background-color: #007acc;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
                .hidden {{
                    display: none;
                }}
            </style>
        </head>
        <body>
            <h1>Task Report for {selected_month_name}</h1>
            <h2>Hours worked by collaborators</h2>
            <div class="chart-container">
                <div class="chart">
                    <canvas id="hoursChart"></canvas>
                </div>
                <div class="chart">
                    <canvas id="taskPieChart"></canvas>
                </div>
            </div>
            <h2>Task Details</h2>
            <div class="dropdown">
                <label for="collaborator-filter">Filter by Collaborator: </label>
                <select id="collaborator-filter">
                    <option value="All">All</option>
        """

        # Add collaborator names to the dropdown
        for name in collaborator_names:
            html_data += f"""
                    <option value="{html.escape(name)}">{html.escape(name)}</option>
            """
        html_data += f"""
                </select>
            </div>
            <div class="table-container">
                <table id="task-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Task</th>
                            <th>Date</th>
                            <th>Type</th>
                            <th>Recorded At</th>
                            <th>Hours</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        # Add rows for each record
        for record in filtered_records:
            html_data += f"""
            <tr data-collaborator="{html.escape(record['Name'])}">
                <td>{html.escape(str(record['Name']))}</td>
                <td>{html.escape(str(record['Task']))}</td>
                <td>{html.escape(str(record['Date']))}</td>
                <td>{html.escape(str(record['Type']))}</td>
                <td>{html.escape(str(record['Recorded At']))}</td>
                <td>{html.escape(str(record['Hours']))}</td>
            </tr>
            """

        html_data += f"""
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="5" style="text-align: right; font-weight: bold;">Total Hours:</td>
                            <td id="total-hours" style="font-weight: bold;">0</td>
                        </tr>
                    </tfoot>
                </table>
            </div>
            <script>
                // Function to calculate total hours based on visible rows
                function calculateTotalHours() {{
                    const rows = document.querySelectorAll('#task-table tbody tr:not(.hidden)');
                    let totalHours = 0;

                    rows.forEach(row => {{
                        const hoursCell = row.querySelector('td:last-child');
                        totalHours += parseFloat(hoursCell.textContent) || 0;
                    }});

                    document.getElementById('total-hours').textContent = totalHours.toFixed(2);
                }}

                // Dropdown filter functionality
                const filterDropdown = document.getElementById('collaborator-filter');
                const tableRows = document.querySelectorAll('#task-table tbody tr');

                filterDropdown.addEventListener('change', function() {{
                    const selectedCollaborator = this.value;
                    tableRows.forEach(row => {{
                        if (selectedCollaborator === 'All' || row.dataset.collaborator === selectedCollaborator) {{
                            row.classList.remove('hidden');
                        }} else {{
                            row.classList.add('hidden');
                        }}
                    }});

                    // Recalculate total hours after filtering
                    calculateTotalHours();
                }});

                // Calculate total hours on page load
                window.onload = calculateTotalHours;

                // Bar Chart Data
                const labels = {names};
                const data = {hours};

                const ctx = document.getElementById('hoursChart').getContext('2d');
                const maxY = Math.max(...{hours}) * 1.15; // Extend Y-axis by 15%
                const hoursChart = new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: labels,
                        datasets: [{{
                            label: 'Hours Worked',
                            data: data,
                            backgroundColor: 'rgba(0, 123, 255, 0.7)',
                            borderColor: 'rgba(0, 123, 255, 1)',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            legend: {{
                                display: false
                            }},
                            tooltip: {{
                                enabled: true
                            }},
                            datalabels: {{
                                color: 'black',
                                anchor: 'end',
                                align: 'end',
                                font: {{
                                    size: 14
                                }},
                                formatter: (value) => Math.round(value)
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                suggestedMax: maxY,
                                title: {{
                                    display: true,
                                    text: '# Hours'
                                }}
                            }},
                            x: {{
                                title: {{
                                    display: true,
                                    text: 'Collaborators'
                                }}
                            }}
                        }}
                    }},
                    plugins: [ChartDataLabels]
                }});

                // Pie Chart with external labels and connecting lines
                const pieCtx = document.getElementById('taskPieChart').getContext('2d');
                const taskPieChart = new Chart(pieCtx, {{
                    type: 'pie',
                    data: {{
                        labels: {task_types_json},
                        datasets: [{{
                            data: {task_hours_json},
                            backgroundColor: [
                                'rgba(255, 99, 132, 0.7)',
                                'rgba(54, 162, 235, 0.7)',
                                'rgba(255, 206, 86, 0.7)',
                                'rgba(75, 192, 192, 0.7)',
                                'rgba(153, 102, 255, 0.7)'
                            ],
                            borderColor: [
                                'rgba(255, 99, 132, 1)',
                                'rgba(54, 162, 235, 1)',
                                'rgba(255, 206, 86, 1)',
                                'rgba(75, 192, 192, 1)',
                                'rgba(153, 102, 255, 1)'
                            ],
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        plugins: {{
                            tooltip: {{
                                enabled: true
                            }},
                            legend: {{
                                position: 'right',
                                labels: {{
                                    font: {{
                                        size: 14
                                    }}
                                }}
                            }},
                            datalabels: {{
                                color: '#000',
                                font: {{
                                    size: 18  // Increased font size
                                }},
                                formatter: (value, context) => {{
                                    const label = context.chart.data.labels[context.dataIndex];
                                    return `${{label}}: ${{value}}%`;
                                }},
                                anchor: 'end',
                                align: 'end',
                                offset: 10,
                            }}
                        }}
                    }},
                    plugins: [ChartDataLabels]
                }});
            </script>
        </body>
        </html>
        """



        # Write to the HTML file
        with open('html_report.html', 'w') as f:
            f.write(html_data)

        # Automatically open the HTML file in the browser
        webbrowser.open('html_report.html', new=2)  # 'new=2' opens in a new tab if possible

        print(f"HTML Report successfully created for {selected_month_name}.")
    except Exception as e:
        print(f"Error creating HTML Report: {e}")

# Main function to display the menu and execute chosen options
def main():
    while True:
        print("\nOptions:")
        print("1. Log Task")
        print("2. View Logs")
        print("3. Export to HTML")
        print("4. Exit")

        choice = input("Choose an option: ")
        if choice == '1':
            log_task()
        elif choice == '2':
            view_logs()
        elif choice == '3':
            export_html()
        elif choice == '4':
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
