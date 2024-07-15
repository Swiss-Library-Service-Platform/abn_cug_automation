import os
import shutil
import git
import config
import logging
from datetime import datetime
from typing import List


class GitRepo:
    """
    Class to handle the git repository

    Attributes:
    -----------
    local_path: str
        The local path to the git repository
    remote_url: str
        The remote url of the git repository
    token_key: str
        The token key to access the git repository
    access_token: str
        The access token to access the git repository
    repo: git.Repo
        The git repository object
    """
    def __init__(self, local_path: str, remote_url: str, token_key: str, access_token: str):
        self.local_path = local_path
        self.remote_url = remote_url
        self.token_key = token_key
        self.access_token = access_token
        if os.path.exists(self.local_path):
            try:
                self.repo = git.Repo(self.local_path)
            except git.exc.InvalidGitRepositoryError:
                self.repo = None
        else:
            self.repo = None

    def delete_local_repo(self) -> None:
        """
        Delete the git repository
        """
        if os.path.exists(self.local_path):
            try:
                shutil.rmtree(self.local_path)
            except PermissionError:
                os.system(f'rmdir /S /Q "{self.local_path}"')

    def clone_repo(self) -> None:
        """
        Fetch the git repository
        """
        self.delete_local_repo()
        self.repo = git.Repo.clone_from(f'https://{self.token_key}:{self.access_token}@{self.remote_url}',
                                        self.local_path)

    def push_repo(self, files_to_commit: List[str]) -> None:
        """
        Push the git repository
        """
        files_to_commit = [f.replace(config.REPOSITORY_PATH, '')[1:] for f in files_to_commit]

        self.repo.index.add(files_to_commit)
        self.repo.index.commit(f'Update task {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')

        try:
            self.repo.remote(name="origin").push()
        except Exception as e:
            logging.error(f"an exception occured: {e}")
        pass