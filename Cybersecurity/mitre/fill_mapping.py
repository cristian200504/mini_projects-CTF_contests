import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font

file_path = "c:/Users/crist/OneDrive/Desktop/mitre/mitre_attck_mapping_flow.xlsx"

# Load workbook
wb = load_workbook(file_path)
ws = wb.active

# Add Mapping name and User name
ws['C3'] = "MITRE ATT&CK flow (Tactics, Techniques, Procedures, Mitigation, Detection, Data sources) for RedTiger Level 1 SQL Injection Lab"
ws['C4'] = "Burlacu Cristian-George"

# The header is at row 7: Tactics | Techniques | Procedures | Mitigation | Detection | Data sources
# We will insert data from row 8 onwards.

data = [
    [
        "TA0001 (Initial Access)", 
        "T1190 (Exploit Public-Facing Application)", 
        "Attacker accesses the vulnerable URL (level1.php) and performs a UNION-based SQL injection on the 'cat' parameter.", 
        "M1050 (Exploit Protection), M1016 (Vulnerability Scanning) - Use parameterized queries and input validation.", 
        "Monitor web server logs for SQL keywords (UNION, SELECT, ORDER BY) in URL parameters.", 
        "DS0015 (Application Log)"
    ],
    [
        "TA0007 (Discovery)", 
        "T1082 (System Information Discovery) / T1087 (Account Discovery)", 
        "Attacker uses 'ORDER BY' and 'UNION SELECT' to enumerate the database structure, finding the number of columns and identifying vulnerable injection points.", 
        "M1026 (Privileged Account Management) - Apply least privilege to DB accounts so they cannot enumerate unrelated schemas.", 
        "Alert on repeated SQL errors (HTTP 500) and abnormal query structures in application logs.", 
        "DS0015 (Application Log), DS0029 (Network Traffic)"
    ],
    [
        "TA0009 (Collection) & TA0006 (Credential Access)", 
        "T1005 (Data from Local System) / T1003 (OS Credential Dumping)", 
        "Attacker extracts the 'username' and 'password' fields from the 'level1_users' table for user 'Hornoxe'.", 
        "M1057 (Data Loss Prevention) - Restrict direct access to sensitive tables like 'level1_users' for the web application user.", 
        "Monitor database for unusual query patterns, such as UNION SELECTs attempting to read credential tables.", 
        "DS0015 (Application Log)"
    ]
]

for row_idx, row_data in enumerate(data, start=8):
    for col_idx, cell_value in enumerate(row_data, start=1):
        ws.cell(row=row_idx, column=col_idx, value=cell_value)

wb.save(file_path)
print("Excel file successfully updated.")
