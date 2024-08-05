# CUG automation abn
* Author: Raphaël Rey (raphael.rey@slsp.ch)
* Date: 2024-07-01
* Version: 1.0.1

## Description
This application is used to update the CUGs in Alma of ABN IZ.
* Verwaltung CUG
* Mediotheken CUG

Each day the script will update the CUGS according to
the configuration and information provided by ABN team.

### Verwaltung CUG
Each user with an email address with domain `ag.ch` must receive the CUG `Verwaltung CUG`.
to find users with email address `ag.ch` the script will use the Alma API to search for
users into Analytics.

### Mediotheken CUG
ABN team provides a list of users who must receive the CUG `Mediotheken CUG`. At IZ level,
the system will try to match user accounts according to first name, last name and birth date.

The script will update the users and store a crypted version of the current state of the users
in order to avoid to test again the same users.

The script will also store the logs of the updates in a log file and a report.

All the files will be uploaded into the git repository of ABN.

## Usage
Schedule the script in a cron table

To start the script:
```bash
python3 task.py
```

## Installation
A `.env` file is required to store the `abn_slsp_exchange_access` variable to have access to the git
repository of ABN.

The library `almapiwrapper` is required to be installed with the required api keys configured.
The script needs API keys to access the Alma API:
* Analytics
* Users

Configuration is to be defined in the `config.py` file.


