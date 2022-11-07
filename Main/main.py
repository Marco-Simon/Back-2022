# Import flask and datetime module for showing date and time
import base64
import io
import os
import re
import json
import imghdr
import sys
import cv2 as cv
import numpy as np
from cmath import acos
import MySQLdb.cursors
from flask_mysqldb import MySQL
from msilib.schema import Component
from matplotlib import pyplot as plt
from datetime import timedelta, datetime 
from flask import Flask,session, Blueprint, request, render_template, redirect, url_for, abort
from imutils.perspective import four_point_transform
from werkzeug.utils import secure_filename
import pytesseract 
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract'


 
HOUR_AND_HALF = 5400
# Initializing flask app
app = Flask(__name__)

app.secret_key = 'your secret key'

app.config['MAX_CONTENT_LENGTH'] = 2048 * 2048
app.config['UPLOAD_EXTENSIONS'] = ['.jpeg', '.jpg', '.png', '.gif']
app.config['UPLOAD_PATH'] = "imgData"


# setup a mysql connection
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'master'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_DB'] = 'schema1'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

@app.route('/', methods=['GET', 'POST'])
def basic():
	return "this is working"
@app.route('/delete', methods=['GET', 'POST'])
def delete():
	msg = False
	if request.method == 'POST' and 'dateC' in request.get_json():
		user = session.get('username')      # gets the users first name
		last_name = session.get('last_name')    # gets the last name .
		time = request.get_json().get('timeC')         # gets the time that was submitted.
		machine = request.get_json().get('machineC')    # gets the machine that was chosen.
		date = request.get_json().get('dateC')      # gets the date that was chosen.
		type = request.get_json().get('type')    # gets the type of machine that was chosen.

		# convert str to datetime
		date = datetime.strptime(date,"%d/%m/%Y").date()

		# convert datetime to str
		date = date.strftime("%Y-%m-%d")
		# verify which type was selected
		if type == 'wash':
			table = "timewash"
		else:
			table = "timedry"
		
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		if table == "timewash":
				cursor.execute('DELETE FROM timewash WHERE Name =%s AND LastName =%s AND machine=%s AND time =%s AND date=%s ', (user, last_name, machine, time, date))
				mysql.connection.commit()
		if table == "timedry":
				cursor.execute('DELETE FROM timedry WHERE Name =%s AND LastName =%s AND machine=%s AND time =%s AND date=%s ',(user, last_name, machine, time, date))
				mysql.connection.commit()
		msg = True
	return {'Message' : msg}
@app.route('/getMachines', methods=['GET', 'POST'])
def getMachines():
	msg = ''
	# type = request.get_json().get('type')
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	# cursor.execute('SELECT Name FROM machines WHERE Type = % s ', (type, ))
	cursor.execute('SELECT Name, Type FROM machines ')
	allMachines = cursor.fetchall()
	print(allMachines)
	msg = allMachines
	mysql.connection.commit()
	return {"Message": msg}

# === Check for currently available machines === ===== ===== ===== ===== ===== ===== =====
@app.route('/isAvailable', methods=['GET', 'POST'])
def isAvailable():
	if request.method == 'POST' and 'type' in request.get_json():
		user = session.get('username')      # gets the users first name
		last_name = session.get('last_name')    # gets the last name .
		time = request.get_json().get('time')         # gets the time that was submitted.
		machine = request.get_json().get('machineI')    # gets the machine that was chosen.
		date = request.get_json().get('date')      # gets the date that was chosen.
		type = request.get_json().get('type')    # gets the type of machine that was chosen.

		# verify which type was selected
		if type == 'wash':
			table = "timewash"
		else:
			table = "timedry"

		if verifyTime(time, machine, date, table):
			return {'Message' : True}
		else: return {'Message' : False}
@app.route('/getTable', methods=['GET', 'POST'])
def getTable():
	msg = ''
	if request.method == 'POST':
		user = session.get('username')      # gets the users first name
		last_name = session.get('last_name')    # gets the last name .
		type = request.get_json().get('type')    # gets the type of machine that was chosen.
		if type == 'wash':
			table = "timewash"
		else:
			table = "timedry"

		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		if table == "timewash":
				cursor.execute('SELECT machine, time, date FROM timewash WHERE Name =%s AND LastName =%s', (user, last_name, ))
				mysql.connection.commit()

		if table == "timedry":
			cursor.execute('SELECT machine, time, date FROM timedry WHERE Name =%s AND LastName =%s',(user, last_name, ))
			mysql.connection.commit()
		allTables = cursor.fetchall()
		
		msg = convertTimeType(allTables[::-1])
		print('line 82--    ',msg)
		# mysql.connection.commit()

	return  {'Message' : msg}


# === Main account page === ===== ===== ===== ===== ===== ===== =====
@app.route('/index', methods=['GET', 'POST'])
def index():
	msg = False
	# if the user chooses a time
	# changed 'appt' to 'time', for convinience
	if request.method == 'POST' and 'time' in request.get_json():
		user = session.get('username')      # gets the users first name
		print("user type: ", type(user) )

		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

		# ======= Minor change =======
		# cursor.execute('SELECT LastName FROM accounts WHERE Name = %s', (user,))
		# mysql.connection.commit()
		# us = cursor.fetchone()
		# for value in us:
		#     last_name = value[1]

		last_name = session.get('last_name')  
		time = request.get_json().get('time')         # gets the time that was submitted
		machine = request.get_json().get('machine')    # gets the machine that was chosen
		date = request.get_json().get('date')      # gets the date that was chosen
		Type = request.get_json().get('type') 
		 # verify which type was selected
		if Type == 'wash':
			table = "timewash"
		else:
			table = "timedry"



		if verifyTime(time, machine, date, table):
			msg = True
			cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			if table == "timewash":
				cursor.execute('INSERT INTO timewash VALUES (NULL, % s, % s, % s,% s, % s)', (user, last_name, machine, time, date))
				mysql.connection.commit()

			if table == "timedry":
				cursor.execute('INSERT INTO timedry VALUES (NULL, % s, % s, % s,% s, % s)',(user, last_name, machine, time, date))
				mysql.connection.commit()

			# saving money
			# cash = 7
			# didhepay = "no"
			# cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			# cursor.execute('INSERT INTO money2 VALUES (NULL, % s, % s, % s, % s, % s, % s % s)',
			#                [user, last_name, date, time, machine, cash, didhepay])
			# mysql.connection.commit()
			print("did pay?")
			return { 'Message' : msg}
		else:
			msg = 'oh no!!!!!!'
		return { 'Message' : msg}

	# if user want to cancel the time he choose NOTE: SEE FUNCTION /delete.

	# if request.method == 'POST' and 'b' not in request.form:
	#     eraselement = request.get_json().get('del')
	#     print("eraselement:", eraselement) 
	#     for i in eraselement:
	#         if i == "=":
	#             x = eraselement.index(i)
	#         if i == ")":
	#             a = eraselement.index(i)

	#     w = eraselement[x + 1:a]
	#     print("w: ", w)
	#     w = int(w)

	#     eraselement = eraselement.replace("(", "", )
	#     eraselement = eraselement.replace(")", "")
	#     eraselement = eraselement.replace("'", "")
	#     eraselement = eraselement.replace(" ", "", 4)
	#     eraselement = list(eraselement.split(","))

	#     timed = timedelta(seconds=w)

	#     if eraselement[4] == 'old washing machine' or eraselement[4] == 'new washing machine':
	#         cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	#         cursor.execute("SELECT * FROM timewash WHERE username =%s AND last_name =%s AND date =%s AND time =%s AND machine =%s",  [eraselement[0], eraselement[1], eraselement[2], timed , eraselement[4]] )
	#         mysql.connection.commit()
	#         erase2 = cursor.fetchall()
	#         id = erase2[0]["id"]
	#         print("id:", id)
	#         cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	#         cursor.execute('DELETE FROM timewash WHERE id = % s', [id])
	#         mysql.connection.commit()

	#     if eraselement[4] == 'old dryer' or eraselement[4] == ' new dryer':
	#         cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	#         cursor.execute("SELECT * FROM timedry WHERE username =%s AND last_name =%s AND date =%s AND time =%s AND machine =%s", [eraselement[0], eraselement[1], eraselement[2], eraselement[3], eraselement[4]])
	#         mysql.connection.commit()
	#         erase2 = cursor.fetchall()
	#         id = erase2[0]["id"]
	#         print("id:", id )
	#         cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	#         cursor.execute('DELETE FROM timedry WHERE id = % s', [id])
	#         mysql.connection.commit()
	#     return render_template('index.html', )


	# if request.method == 'post':
	#     if request.form['b'] == "choose a day to see whos in line?":
	#         thedatyouwhant = request.form['b']
	#         print("thedatyouwhant: ", )


	# # it only work here so please dont touch
	# from datetime import date
	# today = date.today()


	# # if the user wants to see what times are taken
	# if request.method == 'POST' and 'b' in request.form:
	#     today = request.form['b']
	#     print("today1:", today)
	#     day = '2022-07-26'
	#     msg = "hi"
	#     user = session.get('username', None)

	#     # return display(today, user, msg)
	#     # this line gets the current date
	#     print("Today's date:", today)

	#     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	#     cursor.execute("SELECT * FROM timewash WHERE date = % s UNION SELECT * FROM timedry WHERE date = % s", [today, today])
	#     mysql.connection.commit()
	#     times = cursor.fetchall()

	#     if len(times)>0:
	#          print(times)

	#          listOFuser = []
	#          listOFlname = []
	#          listOFdate = []
	#          listOFtime = []
	#          listOFmachine = []
	#          for x in range(len(times)):
	#              listOFuser.append(times[x]['username'])
	#              listOFlname.append(times[x]['last_name'])
	#              listOFdate.append(times[x]['date'])
	#              listOFtime.append(times[x]['time'])
	#              listOFmachine.append(times[x]['machine'])


	#          # takes the lists and places them in a list
	#          # the format of list of list is for the display in the html  file
	#          data = list(zip(listOFuser, listOFlname, listOFdate,  listOFtime, listOFmachine))
	#          print("data:", data)
	#          head = ["name", "last name", "date", "time", "machine", "are you sure"]

	#          return render_template('index.html', data=data, head=head, msg=msg)
	#     else:
	#          mas = " no one is using the machine to-day"

	#          return render_template('index.html',  mas= mas)


	return { 'Message' : msg}


@app.route('/getContact', methods=['GET', 'POST'])
def getContact():
	msg = ''
	user = session.get('username')      # gets the users first name
	last_name = session.get('last_name')    # gets the last name .
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute('SELECT Name, LastName, Email, PhoneNumber FROM accounts WHERE ID > 1 AND Name !=%s AND LastName !=%s', (user, last_name, ))
	mysql.connection.commit()
	account = cursor.fetchall()
	msg = account
	return {'Message' : msg}
####################  Register  ##################################
@app.route('/register', methods=['GET', 'POST'])
def register():
	msg = ''
	if request.method == 'POST' :

		username = request.get_json().get('username')
		last_name = request.get_json().get('lastName')
		password1 = request.get_json().get('password1')
		password2 = request.get_json().get('password2')
		email = request.get_json().get('email')
		phone_number = request.get_json().get('phoneNumber')

		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM accounts WHERE Name = % s', (username,))
		account = cursor.fetchone()

		if account:
			msg = 'Account already exists !'
		elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):   # cheks if starts with @ or has 2 @ or @ is after the dot
			msg = 'Invalid email address !'
		elif not re.match(r'[A-Za-z0-9]+', username):      # checks if it really is only characters upper letters or lower case or numbers
			msg = 'Username must contain only characters and numbers !'
		elif not username or not password1 or not password2 or not email:
			msg = 'Please fill out the form!'
		elif len(username) <= 2 :
			msg = 'Invalid Name!'
		elif len(last_name) <= 2 :
			msg = 'Invalid Name!'
		elif len(phone_number) != 10:
			msg = 'Invalid phone number format'
		elif len(password1) <= 4:
			msg = 'Invalid password!'
		elif password1 != password2:
			msg = 'Please confirm passwords!'
		else:
			cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s, % s, % s, % s)',
						   (username, last_name, email, phone_number, password1))
			mysql.connection.commit()
			msg = True
			return { 'Message' : msg}
	elif request.method == 'POST':
		msg = 'Please fill out the form !'
	return { 'Message' : msg}

####################  login  ##################################
@app.route('/login', methods=['GET', 'POST'])
def login():
	msg = False
	msg2 = False
	if request.method == 'POST' :
		username = request.get_json().get('username')
		password = request.get_json().get('password')
		print(type(username))
		print(type(password))
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM accounts WHERE Name = % s AND Pasword = % s', (username, password))
		# cursor.execute('SELECT * FROM accounts WHERE Name = \'Mordechai\' ;')

		account = cursor.fetchone()

		print(account)
		if account:
			session['logged_in'] = True
			session['id'] = account['ID']
			session['username'] = account['Name']
			session['last_name'] = account['LastName']
			msg = True
			print("--- in if statement ---")
			login.user = account['Name']

			if account['manager'] == 'true':
				msg2 = True
			# # redirects to admins page
			# cursor.execute('SELECT * FROM accounts WHERE Name = % s', (username,))
			# email = cursor.fetchone()
			# if session['username'] == 'shmuel' and email.get("email") == 'shmueladler@hotmail.com' or session['username'] == 'Mordechai' and email.get("email") == 'palmdr433@gmail.com':
			#     return { 'Message' : msg}

			return { 'Message' : msg, 'Message2' : msg2}

		else:
			msg = False
	else:
		if "username" in session:
			return { 'Message' : 'hello', 'Message2' : msg2}
	return { 'Message' : msg, 'Message2' : msg2}


# Route for seeing a data
@app.route('/data')
def get_time():
	# print(data)
	# execute a querey and save it in 'account' variable
	print('check point #2')
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute('SELECT ID, Name, LastName, Email, PhoneNumber, Pasword FROM accounts;')
	account = cursor.fetchall()
	print(account)
	return account[0]
@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	session.pop('id', None)
	session.pop('username', None)
	msg = True
	print("----in logout----")
	return { 'Message' : msg}

# @app.route('/verifyTime', methods =['Get', 'POST'])
# def verifyTime():  
#     if request.method == 'POST':
#         data = request.form

#         # x = datetime.datetime.now()
# 	    # execute a querey and save it in 'account' variable
#     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#     cursor.execute('SELECT time1 FROM accounts;')
#     occupiedTime = cursor.fetchall()

#     inputTime = datetime.timedelta(seconds= 5, minutes= 20, hours = 7)
#     # calculates the difference between the input time
#     #  and the occupied time in the DB. If the input time is earlier than the first time
#     #  in the database, then it will change the sign of the difference.Thus, it will check if the input time 
#     #  clashes with the existing time.
#     for i in range(len(occupiedTime)):    
#         compare = inputTime.total_seconds() - occupiedTime[i]['time1'].total_seconds()
#         if compare < 0: compare = -1*compare
#         if compare < HOUR_AND_HALF :
#             return {'response' : False }
#     return  {'response' : True } 


# the purpose of this function is to change the values from type a datetime to str.
def convertTimeType(arr):
	for x in range(len(arr)):
		arr[x]['date'] = arr[x]['date'].strftime("%d/%m/%Y")
		arr[x]['time'] = json.dumps(arr[x]['time'], default=str)
		arr[x]['time'] = arr[x]['time'][1:len(arr[x]['time'])-4]
	return arr

def verifyTime(thetime, themachine, thedate, table):
	thetime = datetime.strptime(thetime, "%H:%M")

	HOUR_AND_HALF = 5400

	#if request.method == 'POST':
	#data = request.form
	print('check point #1')


	if table =="timewash":

		# x = datetime.datetime.now()
		# execute a querey and save it in 'account' variable
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT time FROM timewash WHERE machine = %s AND date = %s;', [ themachine, thedate])
		occupiedTime = cursor.fetchall()

	if table == "timedry":
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT time FROM timedry WHERE machine = %s AND date = %s;', [ themachine, thedate])
		occupiedTime = cursor.fetchall()


	inputTime = timedelta(hours=thetime.hour, minutes=thetime.minute)
		#datetime.timedelta(seconds=5, minutes=20, hours=7)
	# calculates the difference between the input time
	#  and the occupied time in the DB. If the input time is earlier than the first time
	#  in the database, then it will change the sign of the difference.Thus, it will check if the input time
	#  clashes with the existing time.
	print(occupiedTime)
	for i in range(len(occupiedTime)):
		oct = occupiedTime[i]['time'].total_seconds()
		compare = inputTime.total_seconds() - oct
		if compare < 0: compare = -1 * compare
		if compare < HOUR_AND_HALF:
			return False
		# if occupiedTime[i]['date'] - thedate == 1:
		#    inputTime = inputTime + 43200
		#    oct = occupiedTime[i]['time'].total_seconds() + 43200
		#    compare = inputTime.total_seconds() - oct
		#    if compare < 0: compare = -1 * compare
		#    if compare < HOUR_AND_HALF:
		#        return False
	return True


def auto_canny(image, sigma=0.33):
	# compute the median of the single channel pixel intensities
	v = np.median(image)
	# apply automatic Canny edge detection using the computed median
	lower = int(max(0, (1.0 - sigma) * v))
	upper = int(min(255, (1.0 + sigma) * v))
	edged = cv.Canny(image, lower, upper)
	# return the edged image
	return edged

def getContours(img, imgContour,fullRatio, source):
	
	contour, hierarchy = cv.findContours(img, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
	contour = sorted(contour, key=cv.contourArea, reverse=True)
	receiptCnt = None
	for cnt in contour:
		#techincal data
		area = cv.contourArea(cnt)
		print('area = ',area)
		
		peri = cv.arcLength(cnt, True)
		print('peri = ', peri)
		
		approx = cv.approxPolyDP(cnt, 0.02 * peri, True)
		print(len(approx))
		objCor = len(approx)
		if objCor == 4:
			receiptCnt = approx
			break
		
		x, y, w, h = cv.boundingRect(approx)
	
	if receiptCnt is None:
		cv.imshow('edges', img) 
		cv.waitKey(0) 
		cv.destroyAllWindows()
		raise Exception(("Could not find receipt outline. "
			"Try debugging your edge detection and contour steps."))
	   
	
	# cv.putText(imgContour, objectType, (x + (w//2) - 10, y +(h //2) - 10), cv.FONT_HERSHEY_COMPLEX, 0.5, (0,0,0), 2)
	

	cv.drawContours(imgContour, [receiptCnt], -1, (0,255,0), 2)
	
	x, y, w, h = cv.boundingRect(receiptCnt) 
	# cv.rectangle(imgContour, (x,y), (x + w, y+h), (0,255,0),3)
	# receipt = img2[y: y+ h, x:x + w]
	receipt = wrappingimg(receiptCnt, fullRatio,source)
	# receipt = perspective(receiptCnt)
 
	print(f'{len(contour)} contour(s) found!')
	return receipt

def wrappingimg(cnt, fullRatio,source):
	img = four_point_transform(source, cnt.reshape(4, 2) * fullRatio)
	(height, width, dpth) = img.shape
	rto = 500.0 / width
	dim = (500, int(height * rto))
	img = cv.resize(img, dim)
	return img

def convertText(imgX):
	options = "--psm 4"
	imgX =cv.cvtColor(imgX, cv.COLOR_BGR2GRAY)
	imgX =cv.adaptiveThreshold(imgX,255,cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY,21,10)
	text = pytesseract.image_to_string(imgX, config = options)# show the raw output of the OCR process
	print("[INFO] raw output:")
	print("==================")
	print(text)
	print("\n")
	# define a regular expression that will match line items that include
	# a price component
	pricePattern = r'([0-9]+\.[0-9]+)'
	# show the output of filtering out *only* the line items in the
	# receipt
	print("[INFO] price line items:")
	print("========================")
	for row in text.split("\n"):
	# check to see if the price regular expression matches the current
	# row
		if re.search(pricePattern, row) is not None:

			price = re.search(pricePattern, row).group(0)
			productName = row[: row.rfind(price)]
			if not re.search('SAVE', row):	
				cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
				cursor.execute('INSERT INTO receiptdb VALUES (NULL, % s, % s)', (productName, price))
				mysql.connection.commit()
			
	

def validate_image(stream):
	header = stream.read(512)
	stream.seek(0) 
	format = imghdr.what(None, header)
	if not format:
		return None
	print('== STEP #1.2 ===')
	return '.' + (format)    
def ValidateFile (file):

	fileName = secure_filename(file.filename)
	if fileName != '':
		file_ext = os.path.splitext(fileName)[1]
		if (file_ext not in app.config['UPLOAD_EXTENSIONS']) or file_ext != validate_image(file.stream):
			print('== STEP #1 ===')
			print(file_ext)
			return False
		file.save(os.path.join(app.config['UPLOAD_PATH'], fileName))

		# mysql.connection.commit()
		return  os.path.join(app.config['UPLOAD_PATH'], fileName)
	print('== STEP #2 ===')
	return False
# ==============================================
#                    START
# ==============================================
from PIL import Image
@app.route('/scanningImg', methods=['GET', 'POST'])
def scanningImg():
	msg = False
	if request.method == 'POST':  
		source =  request.files['File']
		imgPath = ValidateFile(source)
		print(type(source))
		if  not imgPath:
			return {'Message': msg}
		# cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		# cursor.execute('select img FROM images WHERE ID >1')
		# mysql.connection.commit()
		# source = cursor.fetchone()

		# 		# Decode the string
		# binary_data = base64.b64decode(source['img'])
		
		# # Convert the bytes into a PIL image
		# source = Image.open(io.BytesIO(binary_data))
		# # img = Image.frombytes("L", (3, 2), source['img'])
		source = cv.imread(imgPath)

		img = source.copy()
		(height, width, dpth) = img.shape
		rto = 500.0 / width
		dim = (500, int(height * rto))
		img = cv.resize(img, dim)

		fullRatio = source.shape[1] / float(img.shape[1])
		print('fullRation ==> ',fullRatio)
		imgContour = img.copy()
		img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

		# kernel = np.ones((5,5),np.uint8)
		# img = cv.dilate(img,kernel,iterations =5)
		img = cv.GaussianBlur(img,(7,7,), cv.BORDER_DEFAULT)
		# img= cv.erode(img,kernel,iterations =5)
		img = auto_canny(img, 0.33)

		output = getContours(img, imgContour, fullRatio,source)
		convertText(output)
		os.remove(imgPath)
		msg = True
	# cv.imshow('edges', img) 
	# cv.imshow('Contour', imgContour)   
	# cv.imshow('imgY', imgY)
	# cv.waitKey(0) 
	# cv.destroyAllWindows()
	# plt.imshow(output)
	# plt.title('Image')
	# plt.imshow(imgY)
	# plt.title('imgY')
	return {'Message' : msg}

# Running app
if __name__ == '__main__':
	app.run(debug=True)
