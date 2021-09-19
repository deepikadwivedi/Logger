# Logger
Flask webserver to retrieve logs using a REST endpoint

<h2>Instructions</h2>
Check out this repo <br>
<code>FLASK_APP=webserver.py FLASK_ENV=development flask run </code>

<h2>REST endpoints</h2>
<h3>/logfiles <br></h3>
<b>Query parameters</b><br>

* filename: filename to retrieve logs from, required
* numlines: number of lines to retrive, positive integer, defaults to 20
