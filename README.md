# RATIB Zakat Tracker
#### Video Demo:  https://youtu.be/OAnOAOdjEt8
#### Description: RATIB is a web app designed to help users easily and accurately calculate and keep track of zakat payments on their salary, based on Shaykh Ibn Baz's fatwa on how to calculate zakat on monthly salaries. Users can set a nisab and track individual salary/income entries for one hijri year, according to the date of crossing nisab threshold. Users can modify or delete individual entries, and also modify nisab at any point - and RATIB will make necessary changes to the savings entries to account for the changes made by the user.

## Features
- Users need to set a nisab amount which can be updated later. When changing the nisab value, previous savings will be adjusted accordingly. If the sum of previous savings was below the previous nisab and remains below the updated nisab, it will continue to be recorded in a table but not tracked for zakat. However, if the savings cross the nisab, all entries will begin being tracked for zakat from the moment they cross the nisab threshold. Due dates of each entry will accurately reflect the date of crossing nisab whenever nisab is changed.
- The dashboard tab allows users to add savings, which will be recorded and displayed in the savings table on the same page. Users can modify the date and initial amount of any income entry, and delete entries as needed.
- When a user inputs a zakat amount, RATIB tracks the amount based on whether it reaches the nisab or not. If the amount reaches the nisab, it is tracked for the following hijri year and displayed in the Zakat Due table when the payment becomes due. Users can then declare the amount as paid, and it will be recorded as paid and displayed on the history tab.
- Any changes made to the savings table - whether by addition, deletion, or modification - are made in relation to the nisab threshold. If the previous savings were below the nisab amount and then any change causes the nisab amount to be crossed, the savings will begin being tracked from the date on which the nisab was crossed, and all subsequent entries will be tracked from their respective entry dates for one hijri year. Alternatively, if the previous total savings already crossed the nisab and then any change causes the total savings to dip below the nisab amount, the zakat tracking will stop. Users can still view entries on the table, but they will be untracked.

## Files
The project files are organized as follows:
- app.py is the Flask application which is the backend server. The app uses sqlalchemy ORM instead of just cs50 SQL for ease of use.
- database.py is used for initiating the database.
- utils.py defines functions that are used in app.py.
- models.py defines the sqlalchemy tables, and create.py is used to create them 
- zakat.db is the database.
- /static containts lux.css for styling and main.js javascript file
- /templates contains the html files for the website.