#################
# Configuration #
#################

# General configuration
IZ = 'ABN'
MEDIOTHEK_USER_GROUP_CODE = 'ABN_Patron-ABN-Mediothek'
HFGS_USER_GROUP_CODE = 'ABN_HFGS_Patron-HFGS'
VERWALTUNG_USER_GROUP_CODE = 'ABN_Patron-Kantonale-Verwaltung'

# Local files path
REPOSITORY_PATH = './abn_slsp_exchange'
PATH_TO_DATA_CURRENT_STATE = f'{REPOSITORY_PATH}/CUG_MEDIO_current_state.csv'
PATH_TO_SOURCE_DATA = f'{REPOSITORY_PATH}/test_list_encrypted.bin'
PATH_TO_REPORT_MEDIOTHEKEN = f'{REPOSITORY_PATH}/report_cug_mediotheken.csv'
PATH_TO_REPORT_VERWALTUNG = f'{REPOSITORY_PATH}/report_cug_verwaltung.csv'

# Git repository configuration
REPOSITORY_URL = 'git.ag.ch/abn/abn_slsp_exchange.git'
REPOSITORY_TOKEN_KEY = 'rw_slsp_token'

# Analytics report configuration
VERWALTUNG_ANALYTICS_REPORT_PATH = ('/shared/Aargauer Kantonsbibliothek 41SLSP_ABN/Reports/'
                                    'SLSP_ABN_reports_on_request/CUG/Users_with_ag_ch_email_and_not_user_group')

# Email configuration
REPORT_DESTINATION = 'raphael.rey@slsp.ch'