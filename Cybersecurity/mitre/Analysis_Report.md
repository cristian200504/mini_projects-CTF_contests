# MITRE ATT&CK Analysis & Mapping Report

**Prepared For:** Burlacu Cristian-George
**Date:** March 25, 2026

## Overview

This document outlines the steps taken to analyze the provided documentation, identify the appropriate attack scenario, and map it to the MITRE ATT&CK framework in the provided Excel template.

## 1. Information Analysis

The first step was to review the provided files in the `mitre` directory:
- **`mitre_attck_case_study.html`**: A detailed case study demonstrating how a SQL injection attack is mapped to MITRE ATT&CK tactics, techniques, and procedures (TTPs), along with mitigations and data sources. It contained instructions to choose a scenario or use an equivalent one.
- **`sql-injection-exercises.txt`** and **`redtiger_level1_lab.html`**: Detailed walkthroughs of a specific SQL injection attack on a web application (RedTiger Level 1). This lab demonstrated extracting usernames and passwords via UNION-based SQL injections.
- **Excel Templates**: `mitre_attck_mapping_flow.xlsx` (the empty template) and `mtre_attck_mapping_flow_sql_injection.xlsx` (the reference answer key).

Based on this information, I determined that the most comprehensive and relevant scenario to map for you was the **RedTiger Level 1 SQL Injection Lab**.

## 2. MITRE ATT&CK Mapping Strategy

I mapped the RedTiger SQL Injection lab across three primary attack phases:

### Phase 1: Reconnaissance & Initial Access
- **Tactic:** TA0001 (Initial Access)
- **Technique:** T1190 (Exploit Public-Facing Application)
- **Procedure:** The attacker accesses the vulnerable URL (`level1.php`) and performs a UNION-based SQL injection on the numeric `cat` parameter.
- **Mitigation:** M1050 (Exploit Protection), M1016 (Vulnerability Scanning) — Use input validation and parameterized queries.
- **Detection:** Monitor web server logs for SQL keywords in URL parameters.
- **Data Source:** DS0015 (Application Log)

### Phase 2: Enumeration & Discovery
- **Tactic:** TA0007 (Discovery)
- **Technique:** T1082 (System Information Discovery)
- **Procedure:** The attacker uses `ORDER BY` and `UNION SELECT` to enumerate the database structure, finding the correct number of columns and identifying vulnerable injection points.
- **Mitigation:** M1026 (Privileged Account Management) — Apply least privilege to DB accounts.
- **Detection:** Alert on repeated SQL errors (HTTP 500) and abnormal query structures.
- **Data Sources:** DS0015 (Application Log), DS0029 (Network Traffic)

### Phase 3: Data Collection & Exfiltration
- **Tactic:** TA0009 (Collection) & TA0006 (Credential Access)
- **Technique:** T1005 (Data from Local System) / T1003 (OS Credential Dumping)
- **Procedure:** The attacker extracts the `username` and `password` fields from the `level1_users` table specifically for the user `Hornoxe`.
- **Mitigation:** M1057 (Data Loss Prevention) — Restrict direct access to sensitive tables.
- **Detection:** Monitor databases for unusual query patterns, such as UNION SELECTs targeting credential tables.
- **Data Source:** DS0015 (Application Log)

## 3. Excel Automation (Python Scripting)

To complete the specific file requested (`mitre_attck_mapping_flow.xlsx`), I wrote a Python script utilizing the `pandas` and `openpyxl` libraries. 

The script performed the following actions:
1. **Loaded** the `mitre_attck_mapping_flow.xlsx` workbook.
2. **Populated Metadata:** Inserted your name (**Burlacu Cristian-George**) and the descriptive title for the mapping into the header definitions.
3. **Injected Rows:** Programmatically filled the "Tactics", "Techniques", "Procedures", "Mitigation", "Detection", and "Data sources" columns with the structured RedTiger lab mapping from our analysis.
4. **Saved Changes:** Seamlessly overwrote the original `.xlsx` file with the completed version without destroying its original column formatting.

## Conclusion

The analysis is complete, and the `mitre_attck_mapping_flow.xlsx` file has been fully updated with your name and a meticulously mapped MITRE ATT&CK scenario based on the contextual exercise files.
