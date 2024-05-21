import os
import subprocess
import csv

print(os.getcwd())
# list_query includes suite queries that you want to run
# free to add or remove
list_query = ["Diagnostics", "analysis", "Exceptions", "experimental", "Expressions", "external", "Filters",
              "Functions", "Imports", "Lexical", "meta", "Metrics", "Numerics", "Resources", "semmle", "Security",
              "Statements", "Summary", "Testing", "Variables"]


query_suites = {
    "python": {
        # "cwe-20": ["codeql/python-queries:Security/CWE-020-ExternalAPIs", "codeql/python-queries:Security/CWE-020"],
        "cwe-20": ["codeql/python-queries:Security/CWE-020"],
        # "cwe-79": ["codeql/python-queries:Security/CWE-079", "codeql/python-queries:experimental/Security/CWE-079", "codeql/python-queries:experimental/Security/CWE-113"],
        "cwe-79": ["codeql/python-queries:Security/CWE-079"],
        "cwe-125": [],
        "cwe-787": []
    },
    "cpp": {
        # "cwe-20": ["codeql/python-queries:Security/CWE-020-ExternalAPIs", "codeql/python-queries:Security/CWE-020"],
        "cwe-20": ["codeql/cpp-queries:Security/CWE/CWE-020"],
        # "cwe-79": ["codeql/python-queries:Security/CWE-079", "codeql/python-queries:experimental/Security/CWE-079", "codeql/python-queries:experimental/Security/CWE-113"],
        "cwe-79": ["codeql/cpp-queries:Security/CWE/CWE-079"],
        "cwe-125": ["codeql/cpp-queries:Security/CWE/CWE-119", "codeql/cpp-queries:Best Practices/Likely Errors"],
        "cwe-787": ["codeql/cpp-queries:Security/CWE/CWE-120"]
    }
}


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
def create_database(file_path, database_folder, source_path, language='python'):
    filename = os.path.splitext(os.path.basename(file_path))[0]
    database_path = os.path.join(database_folder, filename + ".ql")
    if language == "python":
        cmd = ["codeql", "database", "create", database_path, f"--language={language}", "--source-root", source_path,
               "--overwrite"]
    elif language == "cpp":
        cmd = ["codeql", "database", "create", database_path, f"--language={language}", "--source-root", source_path,
               f"--command={os.path.join(os.getcwd(), 'src', 'scripts', 'cpp_compile.sh')} {source_path}", "--overwrite"]
    else:
        raise Exception("Language not support")

    try:
        subprocess.run(cmd, check=True)
        return database_path
    except subprocess.CalledProcessError as e:
        print(f"Error creating database for file {file_path}: {e}")
        return None


# run queries to analyze newly created database
def analyze_database(database_folder, results_folder, database_name, language, cwe_list):
    database_path = os.path.join(database_folder, database_name)
    results_file = os.path.join(results_folder, database_name + ".csv")
    # analyze database using "codeql database analyze" command with suite query python-security-and-quality.qls
    cmd = ["codeql", "database", "analyze", database_path]
    cwe_queries = []
    for cwe in cwe_list:
        if language in query_suites and cwe in query_suites[language]:
            cwe_queries.extend(query_suites[language][cwe])

    if len(cwe_queries) == 0:
        return

    cmd.extend(cwe_queries)
    cmd.extend(["--format=csv", "--output", results_file])
    # cmd = ["codeql", "database", "analyze", database_path,
    #        "codeql/python-queries:Security/CWE-020", "--format=csv", "--output",
    #        results_file]
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


def create_empty_result(results_folder):
    merged_file_name = "codeql.csv"
    merged_file = os.path.join(results_folder, merged_file_name)
    with open(merged_file, "w", newline="") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(
            ["name", "description", "severity", "message", "filename", "start_line", "start_column", "end_line",
             "end_column"])
