import os
import configparser

from pathlib import Path
import git
import github
from github import Github

import time
import datetime

class Backups:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self.target_dir = self.config["BACKUPS"]["target_directory"]
        self.github_token = self.config["GITHUB"]["access_token"]

        self.Ghub = Github(self.github_token)
        self.ghub_user = self.Ghub.get_user()

    def setup(self):
        if not self.target_dir:
            raise ValueError("Please set a target directory.")
        if not os.path.isdir(self.target_dir):
            raise NotADirectoryError(f"'{self.target_dir}' is not a directory.")
        if self.target_dir[-1] != "/":
            raise ValueError(f"'{self.target_dir}' must end with a '/'. Change config.ini")

        dirfiles = (os.scandir(self.target_dir))
        for _file in dirfiles:
            ext = os.path.splitext(_file.path)[1]
            if ext == ".backupverification":
                #verify validity of ver file
                firstline = open(_file.path).readline().strip()
                if firstline == f"Backup Verification File: {self.target_dir}":
                    #ver file is good, go on to verify the remote repo
                    self.verify_github()
                    return
                os.remove(_file.path)
                raise ValueError("System has invalid verification file.")

        #no backup verification file in target dir. create one.
        verfile_content = f"Backup Verification File: {self.target_dir}"
        newfile = open(f"{self.target_dir}/0.backupverification", "w")
        newfile.write(verfile_content)
        newfile.close()

        self.verify_github()

    def upload_verificationfile(self, repo):
        verfile_content = open(f"{self.target_dir}/0.backupverification", "r").read()
        repo.create_file("0.backupverification", "commit backup verification file",
                verfile_content)
        return repo.get_contents("/")

            
    def verify_github(self):
        tardir_name = Path(self.target_dir).name
        repo_name = f"{tardir_name}_backups"

        try:
            repo = self.ghub_user.get_repo(repo_name)
        except github.GithubException:
            repo = self.ghub_user.create_repo(name=repo_name,private=True)

        try:
            repo_contents = repo.get_contents("/")
        except github.GithubException:
            repo_contents = self.upload_verificationfile(repo)
        if not repo_contents:
            repo_contents = self.upload_verificationfile(repo)

        for _file in repo_contents:
            if _file.name == "0.backupverification":
                filecontent =_file.decoded_content.decode("utf-8")
                if filecontent != f"Backup Verification File: {self.target_dir}":
                    raise ValueError("Repository verification file incorrect.")

        self.perform_backup(repo)

    def perform_backup(self, repo):
        date_time = datetime.datetime.now().strftime("%m%d%Y-%H%M%p")
        branch_name = f"backup_{date_time}"
        commit_msg = branch_name

        source = repo.get_branch("main")
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source.commit.sha)

        failed_files = "Files that have failed to upload. Most likely utf-8 can't decode them."

        for (dir_path, dir_names, file_names) in os.walk(self.target_dir):
            dir_path_gh = dir_path.replace(f"{self.target_dir}", "")

            if ".git" in dir_path_gh:
                continue
            if not file_names:
                githubpath = f"{dir_path_gh}/tmp.txt"
                content = "Temp file created by backup software. Original directory empty."
                repo.create_file(githubpath, commit_msg, content, 
                        branch=branch_name)

            for filename in file_names:
                githubpath = f"{filename}"
                if dir_path_gh:
                    githubpath = f"{dir_path_gh}/{filename}"

                try:
                    file_content = open(f"{dir_path}/{filename}", "r").read()
                except UnicodeDecodeError as e:
                    failed_files += f"\n{dir_path}/{filename}"
                    continue

                ghub_files = []
                repo_contents = repo.get_contents("")
                while repo_contents:
                    file_con = repo_contents.pop(0)
                    if file_con.type == "dir":
                        repo_contents.extend(repo.get_contents(file_con.path))
                    else:
                        _file = file_con
                        ghub_files.append(str(_file).replace('ContentFile(path="','').replace('")',''))

                if githubpath in ghub_files:
                    content = repo.get_contents(githubpath)
                    repo.update_file(content.path, commit_msg, file_content, content.sha,
                            branch=branch_name)
                else:
                    repo.create_file(githubpath, commit_msg, file_content,
                            branch=branch_name)
        if len(failed_files.split("\n")) > 1:
            repo.create_file(f"failedfiles.{branch_name}", f"{commit_msg}-Files that failed to backup.", 
                    str(failed_files), branch=branch_name)

def main():
    worker = Backups()
    worker.setup()

if __name__ == "__main__":
    main()
