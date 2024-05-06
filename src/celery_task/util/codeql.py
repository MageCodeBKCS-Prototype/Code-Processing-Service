import os
import subprocess
import csv

# list_query includes suite queries that you want to run
# free to add or remove
list_query = ["Diagnostics", "analysis", "Exceptions", "experimental", "Expressions", "external", "Filters",
              "Functions", "Imports", "Lexical", "meta", "Metrics", "Numerics", "Resources", "semmle", "Security",
              "Statements", "Summary", "Testing", "Variables"]


# create result folder to store processed results
def create_results_folder(folder_path):
    results_folder = os.path.join(folder_path, "results")
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)
    return results_folder


# create folder to store codeql database
def create_database_folder(folder_path):
    database_folder = os.path.join(folder_path, "databases")
    if not os.path.exists(database_folder):
        os.makedirs(database_folder)
    return database_folder


# create database
def create_database(file_path, database_folder, source_path):
    filename = os.path.splitext(os.path.basename(file_path))[0]
    database_path = os.path.join(database_folder, filename + ".ql")
    cmd = ["codeql", "database", "create", database_path, "--language=python", "--source-root", source_path,
           "--overwrite"]
    try:
        subprocess.run(cmd, check=True)
        return database_path
    except subprocess.CalledProcessError as e:
        print(f"Error creating database for file {file_path}: {e}")
        return None


# run queries to analyze newly created database
def analyze_database(database_folder, results_folder, database_name):
    database_path = os.path.join(database_folder, database_name)
    results_file = os.path.join(results_folder, database_name + ".csv")
    # analyze database using "codeql database analyze" command with suite query python-security-and-quality.qls
    cmd = ["codeql", "database", "analyze", database_path,
           "codeql/python-queries:codeql-suites/python-security-and-quality.qls", "--format=csv", "--output",
           results_file]
    # cmd = ["codeql", "database", "analyze", database_path, "codeql/python-queries", "--format=csv", "--output", results_file]
    with open(results_file, "w", newline="") as outfile:
        csv.writer(outfile)

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error analyzing database {database_name}: {e}")


# merge all result files into one files
def merge_results(results_folder):
    merged_file_name = "codeql.csv"
    merged_file = os.path.join(results_folder, merged_file_name)
    with open(merged_file, "w", newline="") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(
            ["name", "description", "severity", "message", "filename", "start_line", "start_column", "end_line",
             "end_column"])

        for file in os.listdir(results_folder):
            if file.endswith(".csv") and file != merged_file_name:
                with open(os.path.join(results_folder, file), "r") as infile:
                    reader = csv.reader(infile, delimiter=',')
                    for row in reader:
                        row[4] = row[4][1:]
                        writer.writerow(row)
