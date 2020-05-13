import os
import time
import datetime
from flask import Flask, session, render_template, request, make_response, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room, send

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

channel_list=[]
channels= {'channel':channel_list}
last_room= {}
msg_hist= {}

@app.route("/")
def index():

	#check if client has logged on session

	signed_in=session.get('displayname')
	

	if signed_in is None:
		return render_template('/create_displayname.html', message="Please create a displayname to continue!")
		# directing client to last chat room
	if signed_in not in last_room:
		return render_template('index.html', message=f"Welcome {signed_in}", channels=channels['channel'], user=signed_in)
	channel= last_room[signed_in]
	return redirect(url_for('channel', channel=channel))

	# resp.set_cookie('username', value=signed_in
# @app.route("/get-cookie")
# def get_cookie():
# 	user = request.cookies.get('username')
# 	return render_template('index.html', message=f"Welcome {user}")


@app.route("/create_displayname", methods=["POST"])
def displayname():
	#create display name using form
	displayname=request.form.get('displayname')
	session['displayname']= displayname
	resp= make_response(render_template('index.html', message=f"Welcome {session['displayname']}", channels=channels['channel']))
	# resp.set_cookie('username', value=displayname)

	return resp


@app.route("/newchannel", methods=["POST"])
def newchannel():
	#add a new channel
	channel_name= request.form.get("channel_new")
	if channel_name in channels['channel']:
		return render_template('index.html', message="channel name exists", channels=channels['channel'])
	#validate input
	if len(channel_name) < 3:
		return render_template('index.html', message="please enter a valid channel name, at least 3 char", channels=channels['channel'])

	#append channel name to global list
	#update channels dict
	channel_list.append(channel_name)
	channels['channel']= channel_list

	return render_template("index.html", channels=channels['channel'])


@app.route("/<channel>")
def channel(channel):
	username=session.get('displayname')

	resp= make_response(render_template("channel.html", channel=channel, username=username, history=msg_hist))
	# resp.set_cookie('room', value=channel)
	
	
	return resp



@socketio.on("send_message")
def message(data):
	message=data['message']
	username=data['username']
	room= data['room']
	t_time= time.gmtime()
	chat_time=time.strftime("%x %X",t_time)
	data['chat_time']= chat_time
	history= []
	# msg_hist[room]= room
	# history.append(f"{username}: {message} [{chat_time}]")
	if room in msg_hist:

		msg_hist[room].append(f"[{chat_time}] {username}: {message}")
		app.logger.info(msg_hist)
	else:
		msg_hist[room]= [f"[{chat_time}] {username}: {message} "]
		app.logger.info(msg_hist)

	# app.logger.info(f"{msg_hist['history']}")



	# channel_list.append(channel)
	# channels['channel'] = channel_list
	app.logger.info(f"{username} wrote {message}")

	socketio.emit('show_message', data, room=room)

@socketio.on('join')
def on_join(data):
	username = data['username']
	room= data['room']
	join_room(room)
	# trying to set username:room dict to remeber last room joined
	# if username in last_room:
	# 	last_room.update({username:room})
	# else:
	# 	last_room.append({username:room})
	app.logger.info(f"{username} has joined {room} room")
	socketio.emit('entry_announcement', data, room=data['room'])
	# socket.emit('annoucement', data)

@socketio.on('leave')
def on_leave(data):
	leave_room(data['room'])
	app.logger.info(f"{data['username']} has left {data['room']}")