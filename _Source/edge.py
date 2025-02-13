#
# Check if ran with admin permissions
#  Get Admin permissions
#
# Check if Edge (Chrome) is installed - C:\Program Files (x86)\Microsoft\Edge\Application\pwahelper.exe
#  Run the uninstall file
#
# Remove Edge Appx packages
# Delete desktop icons
# Delete start menu icons
# Delete startup files
# Delete tasks
# Delete services
# Delete other files / folders
#

import ctypes      # Check if ran as an admin / Window title
import getpass     # Take Permissions
import os          # System OS paths
import sys         # Check if ran as an admin / silent flag
import subprocess  # Run setup.exe file
import winreg      # Modify Windows Registry (Remove Edge Appx Packages)

# Check if ran as admin - Do not force run as admin
if not ctypes.windll.shell32.IsUserAnAdmin(): 
    print("\n Please run as admin.\n")
    os.system("timeout /t 4 >nul")
    sys.exit(1)

# Flags
#   /s = silent (no printing)
silent_mode = False
if len(sys.argv) > 1:
    if sys.argv[1] == '/s':
        silent_mode = True
    elif sys.argv[1] == '/?':
        print("Usage:")
        print(" /s   Silent")
        print("\n")
        sys.exit()
else:
    ctypes.windll.kernel32.SetConsoleTitleW("Bye Bye Edge - 2/12/2025 - ShadowWhisperer")

#Hide CMD/Powershell
def hide_console():
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return startupinfo

#Set Paths
src = os.path.join(sys._MEIPASS, "setup.exe")
PROGRAM_FILES_X86 = os.environ.get("ProgramFiles(x86)", r"C:\\Program Files (x86)")
PROGRAM_FILES = os.environ.get("ProgramFiles", r"C:\\Program Files")
SYSTEM_ROOT = os.environ.get("SystemRoot", r"C:\\Windows")
PROGRAM_DATA = os.environ.get("ProgramData", r"C:\\ProgramData")

#Get user profiles
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList") as key:
    user_profiles = [winreg.EnumKey(key, i) for i in range(winreg.QueryInfoKey(key)[0])]
    USERS_DIR = [winreg.QueryValueEx(winreg.OpenKey(key, profile), "ProfileImagePath")[0] for profile in user_profiles]

################################################################################################################################################

#Edge
EDGE_PATH = os.path.join(PROGRAM_FILES_X86, r"Microsoft\\Edge\\Application\\pwahelper.exe")
if os.path.exists(EDGE_PATH):
    if not silent_mode:
        print("Removing Microsoft Edge")
    cmd = [src, "--uninstall", "--system-level", "--force-uninstall"]
    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    os.system("timeout /t 2 >nul")

#Edge (Appx Packages)  *Ignore 'MicrosoftEdgeDevTools'
user_sid = subprocess.check_output(["powershell", "(New-Object System.Security.Principal.NTAccount($env:USERNAME)).Translate([System.Security.Principal.SecurityIdentifier]).Value"], startupinfo=hide_console()).decode().strip()
output = subprocess.check_output(['powershell', '-NoProfile', '-Command', 'Get-AppxPackage -AllUsers | Where-Object {$_.PackageFullName -like "*microsoftedge*"} | Select-Object -ExpandProperty PackageFullName'], startupinfo=hide_console())
edge_apps = output.decode().strip().split('\r\n')
if output:
    for app in edge_apps:
        if 'MicrosoftEdgeDevTools' in app:
            continue
        # Create registry keys
        winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Appx\\AppxAllUserStore\\EndOfLife\\{user_sid}\\{app}")
        winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Appx\\AppxAllUserStore\\EndOfLife\\S-1-5-18\\{app}")
        winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Appx\\AppxAllUserStore\\Deprovisioned\\{app}")
        # Remove the package for the current user and all users
        subprocess.run(['powershell', '-Command', f'Remove-AppxPackage -Package {app} 2>$null'], startupinfo=hide_console())
        subprocess.run(['powershell', '-Command', f'Remove-AppxPackage -Package {app} -AllUsers 2>$null'], startupinfo=hide_console())

################################################################################################################################################

#Startup - Active Setup
subprocess.run(['reg', 'delete', r'HKLM\SOFTWARE\Microsoft\Active Setup\Installed Components\{9459C573-B17A-45AE-9F64-1857B5D58CEE}', '/f'], startupinfo=hide_console(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

#Desktop Icons
for user_dir in USERS_DIR:
    desktop_path = os.path.join(user_dir, "Desktop")
    for link in [os.path.join(desktop_path, name) for name in ["edge.lnk", "Microsoft Edge.lnk"]]:
        if os.path.exists(link):
            os.remove(link)

#Start Menu Icon
START_MENU_PATH = os.path.join(PROGRAM_DATA, "Microsoft\\Windows\\Start Menu\\Programs\\Microsoft Edge.lnk")
if os.path.exists(START_MENU_PATH):
    os.remove(START_MENU_PATH)

#Tasks - Name
result = subprocess.run(['schtasks', '/query', '/fo', 'csv'], capture_output=True, text=True, startupinfo=hide_console())
tasks = result.stdout.strip().split('\n')[1:]
microsoft_edge_tasks = [task.split(',')[0].strip('"') for task in tasks if 'MicrosoftEdge' in task]
with open(os.devnull, 'w') as devnull:
    for task in microsoft_edge_tasks:
        subprocess.run(['schtasks', '/delete', '/tn', task, '/f'], check=False, stdout=devnull, stderr=devnull, startupinfo=hide_console())

#Tasks - Files
TASKS_PATH = os.path.join(SYSTEM_ROOT, "System32\\Tasks")
for root, dirs, files in os.walk(TASKS_PATH):
    for file in files:
        if file.startswith("MicrosoftEdge"):
            file_path = os.path.join(root, file)
            os.remove(file_path)

#Edge Update Services
service_names = ["edgeupdate", "edgeupdatem"]
for name in service_names:
    if subprocess.run(['sc', 'delete', name], capture_output=True, text=True, startupinfo=hide_console()).returncode == 0:
        subprocess.run(['reg', 'delete', r'HKLM\SYSTEM\CurrentControlSet\Services\edgeupdate', '/f'], startupinfo=hide_console(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['reg', 'delete', r'HKLM\SYSTEM\CurrentControlSet\Services\edgeupdatem', '/f'], startupinfo=hide_console(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

#Folders - C:\Windows\SystemApps\Microsoft.MicrosoftEdge*
SYSTEM_APPS_PATH = os.path.join(SYSTEM_ROOT, "SystemApps")
for folder in next(os.walk(SYSTEM_APPS_PATH))[1]:
    if folder.startswith("Microsoft.MicrosoftEdge"):
        subprocess.run(f'takeown /f "{os.path.join(SYSTEM_APPS_PATH, folder)}" /r /d y && '
                       f'icacls "{os.path.join(SYSTEM_APPS_PATH, folder)}" /grant administrators:F /t && '
                       f'rd /s /q "{os.path.join(SYSTEM_APPS_PATH, folder)}"',
                       shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

#System32 Files
user_name = getpass.getuser()
for f in os.scandir("C:\\Windows\\System32"):
    if f.name.startswith("MicrosoftEdge") and f.name.endswith(".exe"):
        subprocess.run(f'takeown /f "{f.path}" > NUL 2>&1', shell=True)
        subprocess.run(f'icacls "{f.path}" /inheritance:e /grant "{user_name}:(OI)(CI)F" /T /C > NUL 2>&1', shell=True)
        os.remove(f.path)

#Remaining Edge Keys
subprocess.run(['reg', 'delete', r'HKLM\SOFTWARE\WOW6432Node\Microsoft\Edge', '/f'], startupinfo=hide_console(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

#Folders - C:\Program Files (x86)\Microsoft
subprocess.run(["taskkill", "/IM", "MicrosoftEdgeUpdate.exe", "/F"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for folder in ["Edge", "EdgeCore", "EdgeUpdate", "Temp"]:
    folder_path = os.path.join(PROGRAM_FILES_X86, "Microsoft", folder)
    subprocess.run(['rmdir', '/q', '/s', folder_path], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
