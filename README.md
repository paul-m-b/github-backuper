# github-backuper

Github-backuper is a Python script that aims to use Github as a backup service, mostly for text and other similar files. It was built mainly to backup ongoing software development projects.

## Description

It can be important to keep a running backup of your code even if you're already using Github to manage your project. This project automatically creates another github repository and uploads all files to it when it is ran. Therefore, it is best to set it up as a cronjob so that it will run periodically and create a running backup of your work. Each backup is pushed to its own branch that is easily identifiable by the naming structure.

## Getting Started

### Dependencies

* Python 3
* Debian-like OS. 
  * For best results: Ubuntu 20.04.2 LTS
* Github Personal Access Token
  * Should have permissions to read/write/create repositories.
* Additional required dependencies can be installed via requirements.txt

### Running the Program
1. Setup config.ini

    Put the path of the directory you wish to backup in the "target_directory" field. This path should end with "/".
    Put your personal access token in the "access_token" field.

2. `python3 main.py`

    You can also setup a cronjob to run the script at any reasonable interval. 
    
### Help/Contact/Feedback
Create an issue!
