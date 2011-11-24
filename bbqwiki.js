var bbqwiki = bbqwiki || {};

bbqwiki.instanceCount = 0;

bbqwiki.allowTabs = function(e) {
	if (e.keyCode == 9) {
		e.target.value += "\t";
		e.preventDefault();
	}
};

bbqwiki.hasClass = function(node, cls) {
	var data = node.getAttribute("class"),
		i, ii;

	if (data == null || data == "") {
		return false;
	}

	data = data.split(" ");
	for (i = 0, ii = data.length; i < ii; ++i) {
		if (data[i] == cls) {
			return true;
		}
	}
	return false;
};

bbqwiki.removeClass = function(node, cls) {
	var data = node.getAttribute("class"),
		i, ii;

	if (data == null || data == "") {
		return node;
	}

	data = data.split(" ");
	for (i = 0, ii = data.length; i < ii; ++i) {
		if (data[i] == cls) {
			data[i] = "";
			break;
		}
	}
	node.setAttribute("class", data.join(" "));
};

bbqwiki.addClass = function(node, cls) {
	var data = node.getAttribute("class")
	
	if (data == null || data == "") {
		node.setAttribute("class", cls);
		return;
	}
	
	data = data.split(" ");
	data.push(cls);
	node.setAttribute("class", data.join(" "));
};

bbqwiki.toggleTabs = function(container) {
	var ul = container.getElementsByTagName("ul")[0],
		handle = container.getElementsByClassName('bbq-handle')[0];

	if (bbqwiki.hasClass(ul, "open")) {
		bbqwiki.removeClass(ul, "open");
		bbqwiki.removeClass(handle, "open");
	} else { 
		bbqwiki.addClass(ul, "open");
		bbqwiki.addClass(handle, "open");
	}
};

bbqwiki.Wiki = (function() {
	function Wiki(id, article, url) {
		var self = this;
		if (id == null || article == null) {
			return null;
		}

		self.id = id;
		self.article = article;
		self.url = url || "";
		self.instance = ++bbqwiki.instanceCount;

		self.container = null;
		self.generateContainer(self);
		self.window = self.container.getElementsByClassName("bbq-window")[0];
		
		self.showPage(self);
	}

	Wiki.prototype.generateContainer = function(self) {
		var fragment = document.createDocumentFragment(),
			tabs = {'Page': self.showPage, 'Edit': self.showEdit, 'History': self.showHistory},
			div, ul, li, span, handle,
			tab, first, cls;
		
		// ensure the container is empty
		self.container = document.getElementById(self.id);
		bbqwiki.addClass(self.container, "bbq-container");
		self.container.innerHTML = "";

		div = document.createElement('div');
		div.setAttribute("class", "bbq-tabs");
		
		first = true;
		ul = document.createElement('ul');
		for (tab in tabs) {
			li = document.createElement('li');
			li.addEventListener("click", function(func) {
				return function() {
					var selected = self.container.getElementsByClassName("bbq-selected"),
						i, ii;
					for (i = 0, ii = selected.length; i < ii; ++i) {
						bbqwiki.removeClass(selected[i], "bbq-selected");	
					}
					bbqwiki.addClass(this, "bbq-selected");
					func(self);
				};
			}(tabs[tab]), false);
			
			if (first) {
				first = false;
				li.setAttribute("class", "bbq-selected");
			}
			
			span = document.createElement("span");
			span.appendChild(document.createTextNode(tab));
			
			li.appendChild(span);
			ul.appendChild(li);
		}
		div.appendChild(ul);
		
		handle = document.createElement("div");
		handle.setAttribute("class", "bbq-handle");
		span = document.createElement("span");
		span.appendChild(document.createTextNode("\u2665"));
		handle.appendChild(span);
		div.appendChild(handle);

		fragment.appendChild(div);
	
		div = document.createElement("div");
		div.setAttribute("class", "bbq-window");
		fragment.appendChild(div);
	
		self.container.appendChild(fragment);
		handle.addEventListener('click', function() {
			bbqwiki.toggleTabs(self.container)
		}, false);
	};
	
	Wiki.prototype.getEntry = function(self, obj) {
		var xhr = new XMLHttpRequest(),
			formData = new FormData();
		
		xhr.open("POST", self.url + "/get_entry");
		xhr.onreadystatechange = function() {
			if (xhr.readyState == 4) { 
				if (xhr.status == 200) {
					obj.innerHTML = xhr.response;
				} else {
					alert(xhr.status);
				}
			}
		};

		formData.append("title", self.article);
		xhr.send(formData);
	};

	Wiki.prototype.showPage = function(self) {
		self.window.innerHTML = "";
		self.getEntry(self, self.window);
	};

	Wiki.prototype.showEdit = function(self) {
		var fragment = document.createDocumentFragment(),
			div, textarea, input;
		console.log(self);
		self.window.innerHTML = "";
		
		textarea = document.createElement("textarea");
		self.getEntry(self, textarea);
		textarea.addEventListener('keydown', bbqwiki.allowTabs, false);
		textarea.setAttribute("wrap", "off");
		fragment.appendChild(textarea);

		input = document.createElement("input");
		input.setAttribute("type", "button");
		input.setAttribute("value", "Update");
		input.addEventListener("click", function() {
			self.updateEntry(self);
		}, false);
		fragment.appendChild(input);

		self.window.appendChild(fragment);
	};

	Wiki.prototype.updateEntry = function(self) {
		var xhr = new XMLHttpRequest(),
			formData = new FormData();
		xhr.open("POST", self.url + "/update");
		xhr.onreadystatechange = function() {
			if (xhr.readyState == 4) { 
				if (xhr.status == 200) {
					self.showPage(self);
				} else {
					alert(xhr.status);
				}
			}
		};
		formData.append("title", self.article);
		formData.append("content", self.window.getElementsByTagName("textarea")[0].value);
		xhr.send(formData);
	};

	Wiki.prototype.showHistory = function(self) {
		var fragment = document.createDocumentFragment(),
			div, heading;
		self.window.innerHTML = "";
	
		fragment.appendChild(document.createTextNode("No history yet."));

		self.window.appendChild(fragment);
	};

	return Wiki;
})();
