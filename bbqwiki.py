import datetime
import urllib.parse
import re
from diff_match_patch import diff_match_patch
from copy import deepcopy
import lxml.html.clean
#from bs4 import BeautifulSoup
import bottle
from elixir import *
from bottle import get, post, static_file, Bottle, run, request

# TODO use configparser here
# Database stuff
metadata.bind = "sqlite:///bbqwiki.db"


class User(Entity):
	using_options(tablename='users')
	
	username = Field(Unicode(64), primary_key=True)
	password = Field(Unicode(255))
	last_ip = Field(Unicode(64))
	last_logged_in = Field(DateTime)
	edits = OneToMany("History")


class Entry(Entity):
	using_options(tablename='entries')

	title = Field(Unicode(64), primary_key=True)
	content = Field(UnicodeText)
	history = OneToMany("History")


class History(Entity):
	using_options(tablename='history')
	
	entry = ManyToOne("Entry")
	edited_by = ManyToOne("User")
	ip_address = Field(Unicode(64))
	edited_on = Field(DateTime)
	diff = Field(UnicodeText)


def db_init():
	setup_all()
	create_all()

	# Create default admin user if none exist
	#if len(User.query.all()) < 1:
	#	user = User(username="admin", password="admin")
	#	session.commit()


# Data stuff

acceptable_elements = ['a', 'abbr', 'acronym', 'address', 'area', 'b', 'big',
	'blockquote', 'br', 'button', 'caption', 'center', 'cite', 'code', 'col',
	'colgroup', 'dd', 'del', 'dfn', 'dir', 'div', 'dl', 'dt', 'em',
	'font', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 
	'ins', 'kbd', 'label', 'legend', 'li', 'map', 'menu', 'ol', 
	'p', 'pre', 'q', 's', 'samp', 'small', 'span', 'strike',
	'strong', 'sub', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th',
	'thead', 'tr', 'tt', 'u', 'ul', 'var']


acceptable_attributes = ['abbr', 'accept', 'accept-charset', 'accesskey',
	'action', 'align', 'alt', 'axis', 'border', 'cellpadding', 'cellspacing',
	'char', 'charoff', 'charset', 'checked', 'cite', 'clear', 'cols',
	'colspan', 'color', 'compact', 'coords', 'datetime', 'dir', 
	'enctype', 'for', 'headers', 'height', 'href', 'hreflang', 'hspace',
	'id', 'ismap', 'label', 'lang', 'longdesc', 'maxlength', 'method',
	'multiple', 'name', 'nohref', 'noshade', 'nowrap', 'prompt', 
	'rel', 'rev', 'rows', 'rowspan', 'rules', 'scope', 'shape', 'size',
	'span', 'src', 'start', 'summary', 'tabindex', 'target', 'title', 'type',
	'usemap', 'valign', 'value', 'vspace', 'width']



def sanitise_html(fragment):
	fragment = "<div>%s</div>" % fragment
	fragment = lxml.html.clean.clean_html(fragment)
	fragment = lxml.html.clean.autolink_html(fragment)
	return fragment[5:-6]


def get_client_ip():
    x_forwarded_for = request.environ.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.environ.get('REMOTE_ADDR')
    return ip


dmp = diff_match_patch()

def invert_patches(patches):
	new_patches = []
	for old_patch in patches:
		new_diffs = []
		patch = deepcopy(old_patch)
		for diff in patch.diffs:
			new_diffs.append((diff[0] * -1, diff[1]))
		patch.diffs = new_diffs
		new_patches.append(patch)
	return reversed(new_patches)


def make_patch(old, new):
	return dmp.patch_make(old, new)	


def apply_patches(patches, content):
	data, errors = dmp.patch_apply(patches, content)
	if False in errors:
		print("There were errors.")
	return data, errors


def textify_patches(patches):
	return dmp.patch_toText(patches)


# Bottle stuff
app = Bottle()
bottle.debug(True)


@app.post("/get_entry")
def get_entry():
	title = request.forms.get("title", "").strip()
	if title == "":
		return "Error: invalid data."
	
	entry = Entry.query.get(title)
	if entry is None:
		return {"content": ""}
	return entry.content


@app.post("/update")
def update_entry():
	title = request.forms.get("title", "").strip()
	content = request.forms.get("content", "").strip()
	if content == "" or title == "":
		return "Error: invalid data."

	entry = Entry.query.get(title)
	if entry is None:
		entry = Entry(
			title=title,
			content=""
		)

	content = sanitise_html(str(content))
	print(content)
	
	dt = datetime.datetime.utcnow()
	patches = make_patch(entry.content, content)

	# TODO error checking
	entry.content, errors = apply_patches(patches, entry.content)

	history = History(
		entry=entry,
		edited_on=dt,
		ip_address=get_client_ip(),
		diff = textify_patches(patches)
	)
	
	session.commit()

	return "Success"


@app.get('/static/:fn')
def static_files(fn):
	return static_file(fn, root="./static")


def webapp_init():
	run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
	db_init()
	webapp_init()
