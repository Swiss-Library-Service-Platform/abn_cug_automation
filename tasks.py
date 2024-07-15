###############
# Set ABN CUG #
###############

#
# Script uses a provided list to:
# -------------------------------
# - Add CUG (IZ level)
#
# Configuration constants:
# ------------------------
# - IZ: IZ to copy the NZ accounts
# - PATH_TO_DATA_SRC: original data used as source (only used the first time)
# - PATH_TO_DATA_CURRENT_STATE: path to the file used to track updates from the last run
# - NEW_USER_GROUP_CODE: code of the CUG to add to the users
# - JOB_XML_PATH: path to the job used to start the update CUG job
# - LOGICAL_SET_NUMBER: id of the set used to fetch user having already the CUG
# - TEMP_SET_NAME: temporary sert name used for the new set for adding the new CUG
#
# Criterium to process the user:
# ------------------------------
# - First name
# - Last name
# - Birth date
# In case of multi match, no process
#
# Required:
# ---------
# List of users with following columns:
# - Name
# - Vorname
# - Geb.-Datum
# - E-Mail
# - Strichcode
# - Bibliothek
#
# Result list:
# ------------
# A list is produced with additional columns:
# - primary_id: primary ID of alma user account
# - updated: boolean indicating if the user have been processed
# - nz_account_ok: boolean indicating indicating if the NZ account could be found
# - skpipped: user skipped in case of multimatches
#
# Workflow:
# ---------
# 1. Try to find each user in IZ with first name,
#    last name and birth date (skip already updated users and
#    multi matches -> "skkiped" column True)
# 4. Update the list with result of the process
# 5. Fetch set of users with the CUG in IZ
# 6. Compare the primary IDs with the list describing the current state
# 7. Create an itemized set to add the CUG in IZ
#
# How to prevent processing one user?
# -----------------------------------
# - Option 1: remove the user of the list "HFGS_data/CUG_HFGS_current_state.csv"
# - Option 2: set flag "skipped" to True
#
# CUG suppressing:
# ----------------
# NOT ACTIVE YET

# Configuration


# Import libraries
import logging
from datetime import date, datetime
import os
import dotenv
import config
import update_cug.tools as tools
from update_cug.gitrepo import GitRepo

from update_cug import update_mediotheken, update_verwaltung

# Load environment variables with secrets to
# access the git repository and to decrypt the data
dotenv.load_dotenv()
os.environ['GIT_SSL_NO_VERIFY'] = 'true'

# Set current active directory to the script directory
os.chdir(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

repo = GitRepo(
    local_path=config.REPOSITORY_PATH,
    remote_url=config.REPOSITORY_URL,
    token_key=config.REPOSITORY_TOKEN_KEY,
    access_token=os.getenv('abn_slsp_exchange_access')
)

repo.clone_repo()

log_file_path = tools.configure_logger()
logging.info(f'Starting process at {datetime.now()}')

update_mediotheken.workflow()
update_verwaltung.workflow()

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