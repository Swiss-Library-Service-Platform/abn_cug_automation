# This script is used to reset all flags of the current state table to False.

# Import libraries
import logging
from datetime import datetime
import os
import dotenv
import config
import update_cug.tools as tools
from update_cug.gitrepo import GitRepo

from update_cug import update_mediotheken

# Set current active directory to the script directory
os.chdir(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# Load environment variables with secrets to
# access the git repository and to decrypt the data
dotenv.load_dotenv()
os.environ['GIT_SSL_NO_VERIFY'] = 'true'

repo = GitRepo(
    local_path=config.REPOSITORY_PATH,
    remote_url=config.REPOSITORY_URL,
    token_key=config.REPOSITORY_TOKEN_KEY,
    access_token=os.getenv('abn_slsp_exchange_access')
)

repo.clone_repo()

log_file_path = tools.configure_logger()
logging.info(f'Starting process at {datetime.now()}')

update_mediotheken.reset_current_state_table()

logging.info(f'Process ended at {datetime.now()}')

# Encrypt the data
encrypted_log_file_path = tools.encrypt_log_file(log_file_path)
tools.close_loggers()

# Push repository to remote
repo.push_repo([
                config.PATH_TO_DATA_CURRENT_STATE,
                encrypted_log_file_path,
                config.PATH_TO_REPORT_MEDIOTHEKEN,
                config.PATH_TO_REPORT_VERWALTUNG
                ])

# Remove the local repository
repo.delete_local_repo()
