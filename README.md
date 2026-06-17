**Smart File Assistant**

A desktop application built with Python and Tkinter to help you analyze, manage, and organize your files intelligently. This tool automates the tedious process of cleaning up digital clutter by providing AI-driven recommendations and interactive tools.


**1. Features**

* Comprehensive Directory Scans

* Change Tracking
 
* Interactive GUI

* Search and Filter

* Sort by Extension

* One-Click Archiving

* Persistent State

**2. System Architecture**

The application is designed with a modular architecture that separates the user interface from the backend processing engine. This ensures maintainability and clarity in the codebase.

**3. Technologies Used**

Language: Python 3

GUI Framework: Tkinter

Core Libraries:os, json, shutil, datetime

**4. Setup and Installation**

* Clone the repository

git clone https://github.com/Chippo90/Software-and-AI.git

* Navigate to the project directory:

cd Smart-File-Assistant

* Create a virtual environment:

python -m venv .venv

* Activate the virtual environment:

.\.venv\Scripts\activate

* Run the application:

python smart file assistant 2.py

**5. How to Use**

Select Folder to Scan button to choose the directory you want to analyze.

Run Full Analysis button. The application will scan the folder and display a detailed report.

**Review the Report:**

File Changes: See which files have been added, deleted, or modified since the last scan.

Recommendations: Review the list of large or old files suggested for archiving.

Detailed List: View all files with their size and last modified date.

Archive Files: Click the Archive Recommended Files button. 

**6. Future Improvements**

Duplicate File Detection: Implement a feature to find and manage duplicate files.

Advanced Classification: Use machine learning to automatically categorize files (e.g., "Invoices," "Photos," "Source Code").


**7. License**

This project is licensed to Chehab Hany. Gisma University of Applied Sciences
