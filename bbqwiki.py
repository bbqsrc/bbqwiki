import lxml.html
import bottle
from elixir import *
from bottle import get, post, static_file, Bottle, run, request

import datetime
import urllib.parse

# Database stuff
metadata.bind = "sqlite:///bbqwiki.db"

class User(Entity):
	using_options(tablename='users')
	
	username = Field(Unicode(64))
	password = Field(Unicode(255))
	last_ip = Field(Unicode(64))
	last_logged_in = Field(DateTime)
	edits = OneToMany("History")


class Entry(Entity):
	using_options(tablename='entries')

	title = Field(Unicode(64))
	content = Field(UnicodeText)
	history = OneToMany("History")


class History(Entity):
	using_options(tablename='history')
	
	entry = ManyToOne("Entry")
	edited_by = ManyToOne("User")
	ip_address = Field(Unicode(64))
	edited_on = Field(DateTime)
	diff = Field(UnicodeText)


setup_all()
create_all()


# Create default admin user if none exist
if len(User.query.all()) < 1:
	user = User(username="admin", password="admin")
	session.commit()


# Data stuff
BANNED_TAGS = (
	"script",
	"button",
	"input",
	"select",
	"option",
	"video",
	"audio"
)


def get_client_ip():
    x_forwarded_for = request.environ.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.environ.get('REMOTE_ADDR')
    return ip


def sanitise_data(data):
	root = lxml.html.fragment_fromstring(data, create_parent='root')
	for node in root.getiterator():
		if node.tag in BANNED_TAGS:
			node.getparent().remove(node)
	return lxml.html.tostring(root)[6:-7]


# Bottle stuff
app = Bottle()
bottle.debug(True)

@app.post("/update")
def add_entry():
	title = request.forms.get("title", "").strip()
	content = request.forms.get("content", "").strip()
	if content == "" or title == "":
		return "Error: invalid data."

	content = sanitise_data(str(content))
	print(content)
	
	dt = datetime.datetime.utcnow()
	entry = Entry(
		title=title,
		content=content
	)
	history = History(
		entry=entry,
		edited_on=dt,
		ip_address=get_client_ip()
	)
	session.commit()

	return "Success"


@app.get('/static/:fn')
def static_files(fn):
	return static_file(fn, root="./static")


run(app, host="0.0.0.0", port=8080)
