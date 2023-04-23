# RATIB
#### Video Demo:  <URL HERE>
#### Description:

## RATIB Zakat Tracker
RATIB is a web application that accurately tracks zakat and determines whether to track or not depending on whether the nisab amount has been crossed. Users can set the nisab amount, which is the threshold that total savings have to meet in order for zakat payment to be eligible. The app allows users to add, delete, and modify individual income entries and automatically tracks them for one hijri year. Users can view all zakats currently due in the 'zakat due' tab and view the history of paid zakats in the 'history' tab. Additionally, the app offers various other functionalities in the dashboard tab.

## Features
- Users can set the nisab amount
- Add, delete, and modify individual income entries
- Automatic tracking of income entries for one hijri year, depending on whether the nisab threshold has been crossed or not
- View all zakats currently due in the 'zakat due' tab
- View history of paid zakats in the 'history' tab
- Additional functionality is available in the dashboard tab

## Files
The project files are organized as follows:
- app.py is the Flask application which is the backend server. The app uses sqlalchemy ORM instead of just cs50 SQL for ease of use.
- database.py is used for initiating the database.
- utils.py defines functions that are used in app.py.
- models.py defines the sqlalchemy tables, and create.py is used to create them 
- zakat.db is the database.
- /static contains the bootswatch lux file which styles the website using Bootstrap. It also contains the javascript file.
- /templates contains the html files for the website.