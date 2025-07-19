import os
import subprocess
import time


def store_vars():
    # Define the values for the environment variables
    g_additionalModulePath = r'C:\redshift\redshift_v3.0.57\Redshift\Plugins\Maya\2022'
    REDSHIFT_COREDATAPATH = r'C:\redshift\redshift_v3.0.57\Redshift'

    # Set the environment variables in the current process
    os.environ['g_additionalModulePath'] = g_additionalModulePath
    os.environ['REDSHIFT_COREDATAPATH'] = REDSHIFT_COREDATAPATH


print("Environment variables set successfully.")


def launch_maya():
    # Specify the path to the Maya executable
    maya_executable_path = r'C:\Program Files\Autodesk\Maya2022\bin\maya.exe'

    # Launch Maya using subprocess
    subprocess.Popen([maya_executable_path])
    time.sleep(5)  # Wait for Maya to start


store_vars()
launch_maya()


# Get all environment current variables
env_vars = os.environ


# Print each environment variable to double-check if they were stored correctly
for key, value in env_vars.items():
  print(f'{key} = {value}')