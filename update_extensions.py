import os
import time
import multiprocessing
import subprocess

# Constants
SUPER_UPDATER_NAME = "Super-Updater-by-ChatGPT"
PROJECT_NAME = os.path.basename(os.getcwd())
SLEEP_DURATION = 0.1
ERROR_LOG_FILE = "error_log.txt"

# ANSI escape codes for colors
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
BLUE = "\x1b[34m"
MAGENTA = "\x1b[35m"
RESET = "\x1b[0m"

# Function to update the main project's Git repository
def update_main_project():
    print(f"{YELLOW}{SUPER_UPDATER_NAME}{RESET}")
    try:
        # Check if there are any changes in the remote repository
        result = subprocess.run(["git", "fetch", "--dry-run"], check=True, capture_output=True, text=True)
        output = result.stderr.strip()

        # If there are changes, fetch and pull them
        if output:
            subprocess.run(["git", "fetch"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "pull"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print_result(GREEN, f"{PROJECT_NAME} updated successfully.", RESET, "")
        else:
            print_result(BLUE, f"{PROJECT_NAME} is up to date.", RESET, "")

    except subprocess.CalledProcessError as e:
        print_result(RED, f"Error updating main project: ", RESET, f"{e}")
        log_message("ERROR", f"{PROJECT_NAME} update error: {e}")
    except Exception as e:
        print_result(YELLOW, f"Exception updating {PROJECT_NAME}: ", RESET, f"{e}")
        log_message("EXCEPTION", f"{PROJECT_NAME} update exception: {e}")

# Function to update a Git repository located at the specified path
def update_extension_repository(repo_path):
    try:
        # Check if there are any changes in the remote repository
        result = subprocess.run(["git", "fetch", "--dry-run"], cwd=repo_path, check=True, capture_output=True, text=True)
        output = result.stderr.strip()

        # If there are changes, fetch them
        if output:
            subprocess.run(["git", "fetch"], cwd=repo_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "UPDATED", repo_path
        else:
            return "UP_TO_DATE", repo_path
    except subprocess.CalledProcessError as e:
        return "ERROR", repo_path, str(e)
    except Exception as e:
        return "EXCEPTION", repo_path, str(e)

# Function to print a colored status message with an optional repository name
def print_result(status_color, status, repo_name_color, repo_name):
    print(f"{status_color}{status}{RESET} {repo_name_color}{repo_name}{RESET}")

# Function to log a message with a status to the error log file
def log_message(status, message):
    with open(ERROR_LOG_FILE, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {status}: {message}\n")

# Main function
def main():
    # Update the main project first
    update_main_project()

    # Find all Git repositories in the 'extensions' folder
    extensions_folder = "extensions"
    git_dirs = [os.path.join(extensions_folder, d) for d in os.listdir(extensions_folder) if os.path.isdir(os.path.join(extensions_folder, d, ".git"))]
    num_processes = multiprocessing.cpu_count()
    repo_groups = [git_dirs[i:i + num_processes] for i in range(0, len(git_dirs), num_processes)]

    start_time = time.time()

    # Update repositories in parallel using a multiprocessing pool
    with multiprocessing.Pool(processes=num_processes) as pool:
        results = []
        for i, group in enumerate(repo_groups):
            for repo in group:
                results.append(pool.apply_async(update_extension_repository, (repo,)))
            print(f"\x1b[KUpdating repository {i * num_processes + 1} to {(i + 1) * num_processes}...\r", end="")
            while not all(result.ready() for result in results):
                time.sleep(SLEEP_DURATION)
            print("\x1b[K\x1b[1A\x1b[K", end="")
    end_time = time.time()

    # Print a summary of the results
    num_success = 0
    num_up_to_date = 0
    successes = []
    errors = []
    exceptions = []
    up_to_date = []

    for result in results:
        status, repo_path, *message = result.get()
        repo_name = os.path.basename(repo_path)
        if status == "UPDATED":
            num_success += 1
            successes.append(repo_name)
        elif status == "UP_TO_DATE":
            num_up_to_date += 1
            up_to_date.append(repo_name)
        elif status == "ERROR":
            errors.append(repo_name)
            error_message = f"{repo_name} - {message[0]}"
            print_result(RED, f"ERROR {repo_name} - {message[0]}", RESET, "")
            log_message("ERROR", error_message)
        elif status == "EXCEPTION":
            exceptions.append(repo_name)
            exception_message = f"{repo_name} - {message[0]}"
            print_result(YELLOW, f"EXCEPTION {repo_name} - {message[0]}", RESET, "")
            log_message("EXCEPTION", exception_message)

    # Print the fetch report
    print(f"{YELLOW}Fetch report:{RESET}")
    for repo_name in successes:
        print_result(GREEN, "UPDATED", RESET, repo_name)
    for repo_name in up_to_date:
        print_result(BLUE, "UP_TO_DATE", RESET, repo_name)
    for repo_name in errors:
        print_result(RED, "ERROR", RESET, repo_name)
    for repo_name in exceptions:
        print_result(YELLOW, "EXCEPTION", RESET, repo_name)

    # Print a summary of the update process
    print(f"{len(successes)} repositories updated successfully.")
    print(f"{len(errors)} repositories failed with errors.")
    print(f"{len(exceptions)} repositories encountered exceptions.")
    print(f"{len(up_to_date)} repositories already up to date.")
    print(f"\033[KUpdated {len(git_dirs)} Git repositories in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()