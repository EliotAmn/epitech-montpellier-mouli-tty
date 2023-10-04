from colorama import Fore, Back, Style
import requests
import os
import sys
from terminaltables import AsciiTable
import datetime
from rich.progress import track
from terminaltables import AsciiTable
import readline

def updater():
    try:

        lasted = requests.get("https://mtpl.eliotamanieu.fr/epimouli/version").text
        
        if not os.path.isfile(os.path.expanduser('~/.mouliversion')):
            with open(os.path.expanduser('~/.mouliversion'), 'w+') as f:
                f.write("-")
            return
        
        with open(os.path.expanduser('~/.mouliversion'), 'r') as f:
            version = f.read().replace('\n', '').replace(' ', '')
        if lasted != version:
            download_url = "https://mtpl.eliotamanieu.fr/epimouli/lasted"
            print(Fore.YELLOW + "A new version is available, downloading...")
            os.system("wget {} -O ~/.moulitmp".format(download_url))
            os.system("chmod +x ~/.moulitmp")
            os.system("mv ~/.moulitmp ~/epimouli")
            with open(os.path.expanduser('~/.mouliversion'), 'w+') as f:
                f.write(lasted)
            print(Fore.GREEN + "Update successful")
    except:
        pass




def get_trace(mouli_id):

    trace = requests.get("https://tekme.eu/api/profile/moulinettes/{}/trace".format(mouli_id), headers = {'Authorization': TOKEN})
    if trace.status_code != 200:
        print(Fore.RED + "Error while getting trace (status code {})".format(trace.status_code))
        exit(1)

    trace = trace.json()["trace_pool"]

    trace = trace.split(": SUCCESS")
    trace = trace[len(trace) - 1]

    if "# Got" and "# But expected" in trace:
        index1 = trace.find("# Got")
        index2 = trace.find("# But expected")

        trace1 = trace[index1:index2]
        trace2 = trace[index2:]

        #remove first row
        trace1 = trace1[trace1.find("\n"):]
        trace2 = trace2[trace2.find("\n"):]

        table = AsciiTable([["Got (your code result)", "Expected result"], [trace1, trace2]])
        return table.table
    return trace


TOKEN = None


def login(username, password):
    r = requests.post("https://tekme.eu/api/auth/login/bocal", 
                  data = {'username': username, 'password': password})
    if r.status_code == 200:
        print(Fore.GREEN + "Login successful")
        token = r.json()['token']
        with open(os.path.expanduser('~/.moulitoken'), 'w+') as f:
            f.write(token)
    else:
        print(Fore.RED + "Login failed")


arg = sys.argv[1] if len(sys.argv) > 1 else None
if arg == "login":
    username = input("Enter your Epitech email: ")
    password = input("Enter your password: ")
    login(username, password)

if arg == "update":
    updater()
    exit(0)


if os.path.isfile(os.path.expanduser('~/.moulitoken')):
    with open(os.path.expanduser('~/.moulitoken'), 'r') as f:
        TOKEN = f.read().replace('\n', '').replace(' ', '')
else:
    print(Fore.RED + "No token found, please login (mouli login)")
    exit(1)


data = requests.get("https://tekme.eu/api/profile/moulinettes", headers = {'Authorization': TOKEN})
if data.status_code != 200:
    print(Fore.RED + "Error while getting moulinette data (status code {})".format(data.status_code))
    exit(1)
full_data = data.json()



def get_mouli_data(day):
    
    for job in full_data['jobs']:
        if job['project'] == day:
            return job
    return None


jobs_local_ids = {}


def show_modules():
    table_data = [["Module", "Project"]]

    modules = {}

    mid = 0

    for job in full_data['jobs']:
        module_code = job['module']
        project_name = job['project']
        if module_code not in modules:
            modules[mid] = {
                "code": module_code,
                "projects": []
            }
        
        modules[mid]["projects"].append(project_name)
        mid += 1
    
    first = True
    for module in modules:
        module_name = modules[module]["code"]

        for project in modules[module]["projects"]:
            table_data.append([module_name if first else "", project])
            first = False
    table_data = sorted(table_data, key=lambda x: x[1])
    
    for i in range(1, len(table_data)):
        jobs_local_ids[i] = table_data[i][1]
        table_data[i][1] = "{}[{}]{} {}".format(Fore.YELLOW, i, Fore.WHITE, table_data[i][1])

    table = AsciiTable(table_data)
    print(table.table)


header_txt = """==================================
  _____       _ _            _     
 | ____|_ __ (_) |_ ___  ___| |__  
 |  _| | '_ \| | __/ _ \/ __| '_ \ 
 | |___| |_) | | ||  __/ (__| | | |
 |_____| .__/|_|\__\___|\___|_| |_|
       |_|                         

            Moulinette
     https://github.com/EliotAmn
"""
print(Fore.CYAN + header_txt + Fore.WHITE)

show_modules()


suggestions = [proj for proj in jobs_local_ids.values()]

def auto_complete(text, state):
    options = [suggestion for suggestion in suggestions if suggestion.startswith(text)]
    if state < len(options):
        return options[state]
    else:
        return None

readline.set_completer(auto_complete)
readline.parse_and_bind('tab: complete')

mouli_data = {}
while mouli_data.keys().__len__() == 0:
    selectd_project = input("Enter a project name (you can use tab to complete) : ")
    if len(selectd_project) == 1:
        try:
            selectd_project = jobs_local_ids[int(selectd_project)]
        except:
            print(Fore.RED + "Project id not found.")
            continue
    data = get_mouli_data(selectd_project)
    if data is None:
        print(Fore.RED + "Project name not found.")
        continue
    mouli_data = data


# clear terminal
os.system("clear")

print(Fore.CYAN + header_txt + Fore.WHITE)

stats = {
    "FUNCTIONAL": Fore.GREEN + "FUNCTIONAL" + Fore.WHITE,
    "NO TEST PASSED": Fore.RED + "NO TEST PASSED" + Fore.WHITE,
    "NOT REGISTERED": Fore.YELLOW + "NOT REGISTERED" + Fore.WHITE,
    "DELIVERY ERROR": Fore.RED + "DELIVERY ERROR" + Fore.WHITE,
}
m_status = ""

if mouli_data["trace"]["result"] not in stats:
    print(Fore.RED + mouli_data["trace"]['result'] + Fore.WHITE)
    exit(1)

m_status = stats[mouli_data["trace"]["result"]]

if "date" in mouli_data['trace']:
    mouli_time = mouli_data['trace']["date"]
    m_date = datetime.datetime.strptime(mouli_time, "%Y-%m-%dT%H:%M:%S%fZ")
    m_date += datetime.timedelta(hours=2)
    m_date = m_date.replace(microsecond=0)
else:
    m_date = "-"

m_title = mouli_data['trace']['instance']["projectName"] if "instance" in mouli_data['trace'] else mouli_data['project']

skils = mouli_data['trace']["skills"] if "skills" in mouli_data['trace'] else []
m_percent = mouli_data['trace']["total_tests_percentage"] if "total_tests_percentage" in mouli_data['trace'] else 0



table_data = [
    ['Skill', 'State']
]

for skill in skils:
    total_tests = len(skill['tests'])
    total_tests_passed = len([test for test in skill['tests'] if test['passed'] == True])
    all_passed = total_tests == total_tests_passed

    s_title = skill['name']
    s_state = "{}{}{} ({}/{})".format(
        Fore.GREEN if all_passed else Fore.RED,
        "PASSED" if all_passed else "FAILED",
        Fore.WHITE,
        total_tests_passed,
        total_tests
    )

    table_data.append([s_title, s_state])


table = AsciiTable(table_data)

print("\n\n======== LASTED MOULI INFO ========\n")
print("{}{}{} : {}".format(Fore.YELLOW, "Project", Fore.WHITE, Fore.CYAN + str(m_title) + " ({})".format(mouli_data['id']) + Fore.WHITE))
print("{}{}{} : {}".format(Fore.YELLOW, "Date", Fore.WHITE, Fore.GREEN + str(m_date) + Fore.WHITE))
print("{}{}{} : {}".format(Fore.YELLOW, "Status", Fore.WHITE, m_status))
print("{}{}{} : {}".format(Fore.YELLOW, "Commit", Fore.WHITE, mouli_data["trace"]['gitCommit'] if "gitCommit" in mouli_data["trace"] else "-"))

for n in track(range(100), description="{}{}{} : {}".format(Fore.YELLOW, "Passed tests", Fore.WHITE, "")):
    if n > m_percent:
        break

print("\n")





def display_strings_in_columns(str1, str2):

    lines1 = str1.split('\n')
    lines2 = str2.split('\n')

    for i in [0, 1, 2]:
        if lines1[i].endswith('    '):
            lines1[i] = lines1[i][:-4]
    

    max_length1 = max(len(line) for line in lines1) + 10
    
    
    for line1, line2 in zip(lines1, lines2):
        if line1 == "":
            line1 = " "*max_length1
        formatted_line1 = "{:<{width}}".format(line1, width=(max_length1 - len(line1)))
        print(f"{formatted_line1}      {line2}")
    
    for line2 in lines2[len(lines1):]:
        spaces = "."*(max_length1-len(line2))
        print(f"{spaces} ~~~~ {line2}")

    for line1 in lines1[len(lines2):]:
        formatted_line1 = "{:<{width}}".format(line1, width=(max_length1 - len(line1)))
        print(f"{formatted_line1}      ")

    
    return ""
table_skils = table.table


table_data = [
    ['Skill', 'Test', "Result"]
]


for skill in mouli_data['trace']["skills"] if "skills" in mouli_data['trace'] else []:
    skill_name = "{}{}{}".format(Fore.YELLOW, skill['name'], Fore.WHITE)
    name_written = False
    for test in skill['tests']:
        if test['passed'] == False:

            if test['crashed']:
                result = "{}{}{}".format(Back.RED, "CRASHED", Back.RESET)
            else:
                result = "{}{}{}".format(Fore.RED, "FAILED", Fore.WHITE)

            if not name_written:
                table_data.append([skill_name, "{}{}{}".format(Fore.RED, test['name'], Fore.WHITE), result])
                name_written = True
            else:
                table_data.append(["", "{}{}{}".format(Fore.RED, test['name'], Fore.WHITE), result])




table = AsciiTable(table_data)
table_tests = table.table

table_skils = "Skills overview:\n" + table_skils
table_tests = "Tests failed:\n" + table_tests


print(display_strings_in_columns(table_skils, table_tests))


print("\n")


opentrace = input("Open trace ? (y/n)")
if opentrace == "y":
    trace = get_trace(mouli_data['id'])
    with open(os.path.expanduser('~/.moulitrace'), 'w+') as f:
        f.write(trace)
    os.system("emacs ~/.moulitrace --eval '(setq buffer-read-only t)'")