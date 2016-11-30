#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import flash, Flask, request, render_template, g, redirect, Response, url_for, session, Blueprint
from flask.ext.login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
import datetime


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following uses the postgresql test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of: 
#
#     postgresql://sw3013:35hm4@104.196.175.120/postgres
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# Swap out the URI below with the URI for the database created in part 2
DATABASEURI = "postgresql://sw3013:35hm4@104.196.175.120/postgres"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


#
# START SQLITE SETUP CODE
#
# after these statements run, you should see a file test.db in your webserver/ directory
# this is a sqlite database that you can query like psql typing in the shell command line:
# 
#     sqlite3 test.db
#
# The following sqlite3 commands may be useful:
# 
#     .tables               -- will list the tables in the database
#     .schema <tablename>   -- print CREATE TABLE statement for table
# 
# The setup code should be deleted once you switch to using the Part 2 postgresql database
#
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
#
# END SQLITE SETUP CODE
#


###
# This part deal with LOGIN
###
app.secret_key = 's3cr3t'
login_manager = LoginManager()
login_manager.session_protection = 'basic'
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

# auth = Blueprint('auth', __name__)

@app.route('/login_page')
def login_page():
	return render_template('login.html')

# @auth.route('/login', methods=['POST', 'GET'])
@app.route('/login', methods=['POST', 'GET'])
def login():
    """
    1. get username, pwd from form
    2. validate info
    3. log user in -> index
    """
#     username = request.cookies.get('username')
#     print 'login username:', username # None
#     print username == None  # True
    if request.form['username'] == None:
  		return render_template('login.html')
  
    error = None
    if request.method == 'POST':
        if valid_login(request.form['username'],
                       request.form['password']):
            print "Valid User!"
            
            login_user(load_user(request.form['username']))
            print "Succesfully log in! %s" %str(request.form['username'])
            flash('Logged in successfully.')
            
            return redirect('/index')
        else:
            error = 'Invalid username/password'
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return render_template('login.html', error=error)
  
    
def valid_login(username, password):
	username = str(username)
	print 'input username', username 
	print 'input password', password
	cursor = g.conn.execute("SELECT password FROM users WHERE username='%s'" %username)
	if cursor.rowcount == 0:
		print "no row in valid_login"
		return False
	actual_pwd = str(list(cursor.first())[0]).rstrip()
	print 'actual password', actual_pwd
	if actual_pwd != str(password):
		return False
	else:
		return True
    
@login_manager.user_loader
def load_user(username):
    """
    input:  a unicode
    return: user object
    """
    username = str(username)
    
    # by default:
    if username == "1":
    	return User(username, None, None)
    
    # with username input
    cursor = g.conn.execute("SELECT uid, password FROM users WHERE username='%s'" %username)
    if cursor.rowcount == 0:
    	cursor.close()
    	raise ValueError("no row")
    temp = list(cursor.first())
#     print "THE cursor conten", temp
    uid, pwd = [str(i).rstrip() for i in temp]
    uid = int(uid)
    
    curr_user = User(username, pwd, uid)
#     curr_user = User(username)
#     print "Successfully load user"
    return curr_user


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
	logout_user() 
	flash('Logged in successfully.')
	return redirect('/')

# user models
class User(UserMixin):
	def __init__(self, username, pwd, uid):
# 	def __init__(self, username):
		self.id = username
		self.password = pwd
		self.id = str(uid)
# #	
# 	@property
# 	def is_enticated(self):
# 		return True
# 		
# 	@property
# 	def is_active(self):
# 		return True
# 		
# 	@property
# 	def is_anonymous(self):
# 		return False
# 
# 	def get_id(self):
# 		return str(self.id)
            

###
# Back to web application
###

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
@app.route('/index')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
#   print request.args

  # DEBUG: login cookie
  print 'current user index', current_user.get_id()

  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT username from users;")
  names = []
  for result in cursor:
    names.append(result['username'])  # can also be accessed using result[0]
  cursor.close()

  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#

@app.route('/signup')
def signup():
	return render_template("signup.html")
  
@app.route('/sign_to_db', methods=['POST'])
def sign_to_db():
  username = request.form['username']
  password = request.form['password']
  email = request.form['email']
  phone = request.form['phone']
  address = request.form['address']
  
  # find maximum uid
  cursor = g.conn.execute("SELECT MAX(uid) FROM users")
  if cursor.rowcount:
    max_uid = list(cursor.first())[0]
  else:
    max_uid = 0
    cursor.close()
  
  # insert user to db
  cmd = 'INSERT INTO users VALUES (:uid, :username, :password, :email, :phone, :address)';
  try:
  	g.conn.execute(cmd, uid=max_uid+1, username=username, password=password, email=email, phone=phone, address=address)
  	return redirect('/')
  except:
    return render_template('error.html'), 404
    

@app.route('/about')
def about():
	# DEBUG: login cookie
	username = request.cookies.get('username')
	print 'username:', username

	return render_template("about.html")

@app.route('/allDB')
def allDB():
	# DEBUG: login cookie
	username = request.cookies.get('username')
	print 'username:', username

	# Users
	users = generate_table('users')
	# Buyers
	buyers = generate_table('buyer')
	# SELLER
	sellers = generate_table('seller')
	# STD INFO
	std_info = generate_table('standard_info')
	# products_post_has
	pro_post = generate_table('products_post_has')
	# order_contains_prod_makes_fb_uses
	order_fb = generate_table('order_contains_prod_makes_fb_uses')
	# COUPON 
	coupons = generate_table('coupon')


	context = dict(username=users, buyers=buyers, sellers=sellers, std_info=std_info, pro_post=pro_post, order_fb=order_fb, coupon=coupons)
	return render_template("allDBfile.html", **context)

def generate_table(table_name):
	'''
    take a table name,
    return a table content in a list w/o header
    '''
	cursor = g.conn.execute("SELECT * from %s;" % table_name)
	cols = list(cursor.keys())
	table_content = [cols]
	
	for result in cursor:
		'''
		rec = []
		for i in range(len(result)):
		rec.append(result[i])
		table_content.append(rec)
		'''
		table_content.append(list(result))
	cursor.close()
	return table_content

# Products page
@app.route('/products')
def products():
	# DEBUG: login cookie
	username = request.cookies.get('username')
	print 'username:', username

	cursor = g.conn.execute("WITH temp1(username, sid, pid, iid, pname, price, pdscp) AS (SELECT u.username, s.sid, p.pid, p.iid, p.pname, p.price,p.customized_description AS pdscp FROM products_post_has p, users as u, seller as s WHERE p.number > 0 AND u.uid=s.uid AND s.sid=p.sid), fb_count(pid, cnt) AS (SELECT pid, COUNT(*) AS cnt FROM order_contains_prod_makes_fb_uses GROUP BY pid) SELECT t.pname, t.price, t.pdscp,  t.username, t.pid, t.iid, c.cnt, t.sid FROM temp1 as t LEFT JOIN fb_count AS c ON t.pid=c.pid")
	prods = []
	for record in cursor:
		record = list(record)
		rec = {'username':record[3], 'fb':record[6], 'product_name':record[0], 'price':record[1], 'product_dscp':record[2],'pid':record[4], 'iid':record[5], 'cnt':record[6], 'sid':record[7]}
		prods.append(rec)
	cursor.close()
	return render_template('products.html', products = prods)

@app.route('/products/prod-<num>')
def product_single(num):
	"""
	num : int pid
	"""
	# DEBUG: login cookie
	username = request.cookies.get('username')
	print 'username:', username

	# extract and assign information for this product
	cursor = g.conn.execute("SELECT p.sid, p.pid, p.pname, p.price, p.customized_description, u.username, i.original_price, i.iid, i.brand, i.link FROM products_post_has p, users u, seller s, standard_info i WHERE u.uid=s.uid AND s.sid=p.sid AND p.iid=i.iid AND pid=%s;" % num)
	assert cursor.rowcount == 1
	result = cursor.first()
	sid, pid, product_name, price, description, post_username, orig_price, iid, brand, link = list(result)

	# extract review data and buyer name for this product
	cursor = g.conn.execute("SELECT u.username, f.f_time, f.rating, f.amount, f.reviews FROM order_contains_prod_makes_fb_uses f, buyer b, users u WHERE f.pid=%s AND f.bid=b.bid AND b.uid=u.uid" % num)
	fb_results = []
	if cursor.rowcount:
		for fb in cursor:
			fb = list(fb)
			fb_single = {'fb_user':fb[0], 'f_time':fb[1], 'rating':fb[2], 'amount':fb[3], 'review':fb[4]}
			fb_results.append(fb_single)
	cursor.close()

	return render_template('product-single.html', num=num, product_name=product_name, price=price, post_username=post_username, iid=iid, brand=brand, orig_price=orig_price, description=description, fb=fb_results, link=link, num_fb=len(fb_results))

@app.route('/products/make-order-prod-<num>')
def make_order(num):
    # DEBUG: login cookie
	username = request.cookies.get('username')
	print 'username:', username

	# extract and assign information for this product
	cursor = g.conn.execute("SELECT p.sid, p.pid, p.pname, p.price, p.number, p.customized_description, u.username, i.original_price, i.iid, i.brand, i.link FROM products_post_has p, users u, seller s, standard_info i WHERE u.uid=s.uid AND s.sid=p.sid AND p.iid=i.iid AND pid=%s;" % num)
	assert cursor.rowcount == 1
	result = cursor.first()
	sid, pid, product_name, price, number, description, post_username, orig_price, iid, brand, link = list(result)

	return render_template('order-single.html', num=num, product_name=product_name, price=price, number=number, post_username=post_username, iid=iid, brand=brand, orig_price=orig_price, description=description, link=link)


@app.route('/profiles')
def profiles():
	# DEBUG: login cookie
	username = request.cookies.get('username')
	print 'username:', username

	cursor = g.conn.execute("SELECT uid, username, address, phone, email FROM users;")
	results = []
	for rec in cursor: 
		rec = list(rec)
		results.append({'uid':rec[0], 'username':rec[1], 'address':rec[2], 'phone':rec[3], 'email':rec[4]})
	return render_template('profiles.html', results=results)
  
    
@app.route('/profiles/<username>')
@app.route('/<username>')
def profile(username):
	"""
	username : str
	"""
	# DEBUG: login cookie
	#   username = request.cookies.get('username')
	#   print 'username:', username
	if username == None:
		return login
	
	
	username = str(username)
	# show user information on this page
	cursor = g.conn.execute("SELECT u.uid, u.email, u.address, u.phone FROM users AS u WHERE u.username='%s';" % username)
	if cursor.rowcount == 1:
		result = cursor.first()
		uid, email, addr, phone = list(result)
	else:
		cursor.close()
		return page_not_found('no user record')

	return render_template('profile-single.html', username=username, uid=uid, email=email, addr=addr, phone=phone)



@app.route('/coupons')
def coupons():
	# DEBUG: login cookie
	#   username = request.cookies.get('username')
	#   print 'username:', username

  
	cursor = g.conn.execute("SELECT c.cid, c.description, c.discount, c.condition, c.expired_time FROM coupon c;")
	results = []
	for rec in cursor:
		rec = list(rec)
		results.append({'code':rec[0], 'dscp':rec[1], 'discount':rec[2], 'condition':rec[3], 'expired_time':rec[4]})
	cursor.close()
	return render_template('coupons.html', coupons=results)

@app.route('/orders')
def orders():
	# DEBUG: login cookie
	username = request.cookies.get('username')
	print 'username:', username

	cursor = g.conn.execute("SELECT o.oid, u1.username, u2.username, o.o_time, o.completed, o.f_time FROM order_contains_prod_makes_fb_uses o, products_post_has p, seller s, buyer b, users u1, users u2 WHERE p.pid=o.pid AND o.sid=s.sid AND u1.uid=s.uid AND o.bid=b.bid AND b.uid=u2.uid;")
	results = []
	for rec in cursor:
		oid, seller, buyer, o_time, completed, reviewd = list(rec)
		results.append({'oid': oid, 'seller':seller, 'buyer':buyer, 'o_time':o_time, 'completed':completed, 'reviewd':reviewd})
	return render_template('orders.html', results=results)

# submit an order
# 1. check information validation
# 2. insert into table
# 3. redirect to seller info
# ------
@app.route('/submit_order', methods=['POST'])
def submit_order():
# DEBUG: login cookie
#   username = request.cookies.get('username')
#   print 'username:', username
  username = str(request.form['username'])
  
  # validate coupon code
  code = request.form['code']
  cursor = g.conn.execute("SELECT c.discount FROM coupon c WHERE c.cid='%s' AND c.amount>0" % code)
  if cursor.rowcount == 0:
    # no such coupon
    code = 'OVER1'
    discount = 1.
    cursor.close()
  else:
    discount = float(list(cursor.first())[0])
    
  
    
  # get current oid
  cursor = g.conn.execute("SELECT MAX(oid) FROM order_contains_prod_makes_fb_uses")
  if cursor.rowcount:
    max_oid = list(cursor.first())[0]
  else:
    max_oid = 0
    cursor.close()
  
  # get buyer information
  username = request.form['username']
  
  # LOGIN ISSUE 
#   login_user = request.cookies.get('username')
#   if login_user == None:
# 	return redirect('/')
#   if username != login_user:
# 	return page_not_found('Ooops, seems like you are not the buyer')
    
  cursor = g.conn.execute("SELECT b.bid FROM users u, buyer b WHERE u.uid=b.uid AND u.username='%s'" % username)
  if cursor.rowcount:
    bid = list(cursor.first())[0]
  else:
    bid_cur = g.conn.execute('SELECT MAX(bid) FROM buyer')
    if bid_cur.rowcount:
      max_bid = list(bid_cur.first())[0]
    else:
      max_bid = 0
      bid_cur.close()
    bid = max_bid + 1
  
  # total price and payment
  amount = int(request.form['amount'])
  pid_cur = g.conn.execute("SELECT p.price, p.sid, p.number FROM products_post_has p WHERE p.pid=%s" % request.form['pid'])
  if pid_cur.rowcount:
    unit_price, sid, number = list(pid_cur.first())
    unit_price = float(unit_price)
    number = int(number)
  else:
    pid_cur.close()
  total_price = amount * unit_price
  actual_payment = total_price * discount
  
  # redirect to seller profile
  sid_cur = g.conn.execute("SELECT u.username FROM seller s, users u WHERE u.uid=s.uid AND s.sid='%s'" %sid)
  if sid_cur.rowcount:
    seller_name = list(sid_cur.first())[0]
  else: 
    sid_cur.close()
  
  
  cmd = 'INSERT INTO order_contains_prod_makes_fb_uses VALUES (:oid, :cid, :pid, :bid, :sid, :o_time, :amount, :total_price, :actual_payment, :completed, :rating, :f_time, :reviews)';
  g.conn.execute(text(cmd), oid=max_oid+1, cid=code, pid=request.form['pid'], bid=bid, sid=sid, o_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), amount=request.form['amount'], total_price=total_price, actual_payment=actual_payment, completed='False', rating=None, f_time=None, reviews=None);
  return redirect('/%s' %seller_name)

# write_review
@app.route('/write_review_<oid>')
def write_review(oid):
  """
  oid : int 
  """
  oid = int(oid)
  cursor = g.conn.execute("SELECT u1.username, u2.username, o.o_time FROM order_contains_prod_makes_fb_uses o, products_post_has p, seller s, buyer b, users u1, users u2 WHERE p.pid=o.pid AND o.sid=s.sid AND u1.uid=s.uid AND o.bid=b.bid AND b.uid=u2.uid AND o.oid=%s;" % oid)
  assert cursor.rowcount == 1
  result = cursor.first()
  seller, buyer, o_time = list(result)
  return render_template('write_review.html', oid=oid, seller=seller, buyer=buyer, o_time=o_time)

@app.route('/submit_review', methods=['POST'])
def submit_review():
  buyer = request.form['buyer']
  
  # LOGIN ISSUE
#   login_user = request.cookies.get('username')
#   if login_user == None:
#     return redirect('/')
#   if login_user != buyer:
#     return page_not_found('Ooops, seems like you are not the buyer')

  oid = request.form['oid']
  rating = request.form['rating']
  review = request.form['review']
  cmd = "UPDATE order_contains_prod_makes_fb_uses SET completed='t', rating=(:rating), reviews=(:review), f_time=(:f_time) WHERE oid=%s;" %oid
#   print oid, rating, review
#   print cmd
  g.conn.execute(text(cmd),rating=rating, review=review, f_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'));
  return redirect('/index')

# upload stuff
@app.route('/stuff')
def stuff():
  return render_template('upload.html')

@app.route('/insert_stuff', methods=['POST'])
def insert():
#########################
  # LOGIN ISSUE
#   login_user = str(request.cookies.get('username'))
#   if login_user == None:
#     return redirect('/signup')
#########################
  username = str(request.form['username'])
  
  name = str(request.form['name'])
  size = str(request.form['size'])
  original_price = str(request.form['original_price'])
  weight = float(request.form['weight']) if request.form['weight'] else None
  link = str(request.form['link'])
  brand = str(request.form['brand'])
  customized_description = str(request.form['customized_description'])
  price = str(request.form['price'])
  number = str(request.form['number'])
  print name, original_price, size, weight,link,brand

  cursor = g.conn.execute("SELECT MAX(s.iid) from standard_info as s")
  new_iid = 0
  for result in cursor:
    new_iid = str(int(result.values()[0]) + 1)
  print new_iid
  cursor.close()

  #(iid, brand, size, original_price, weight, name,link)
  cmd = 'INSERT INTO standard_info VALUES (:iid, :brand, :size,:original_price, :weight, :name, :link)';
  #cmd = 'INSERT INTO order_contains_prod_makes_fb_uses VALUES (:oid, :cid, :pid, :bid, :sid, :o_time, :amount, :total_price, :actual_payment, :completed, :rating, :f_time, :reviews)';
  #g.conn.execute(text(cmd), oid=max_oid+1, cid=code, pid=request.form['pid'], bid=bid, sid=sid, o_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), amount=request.form['amount'], total_price=total_price, actual_payment=actual_payment, completed='False', rating=None, f_time=None, reviews=None);


#   try:
  g.conn.execute(text(cmd), iid = new_iid, brand = brand, size = size, original_price = original_price, weight =weight, name = name, link = link);
  # except:
#     render_template('error.html'), 404

  cursor = g.conn.execute("SELECT MAX(U.pid) from products_post_has as U")
  new_pid = 0
  for result in cursor:
    new_pid = str(int(result.values()[0]) + 1)
  print new_pid
  cursor.close()

#   sid = 0
#   print "loginin", len(login_user)
#   if len(login_user) == 3:
#     sid = login_user[2]
#   else:
#     render_template('error.html'), 404
  # else:
  #   cursor = g.conn.execute("SELECT MAX(s.sid) from seller as s")
  #   for result in cursor:
  #     sid = str(int(result.values()[0]) + 1) 

# find uid
  cursor = g.conn.execute("SELECT s.sid, u.uid FROM seller s RIGHT JOIN users u ON s.uid=u.uid WHERE u.username='%s'" %username)
  if cursor.rowcount == 0:
    return page_not_found("No such user")
  else:
    sid, uid = list(cursor.first())
    if not sid:
      cursor = g.conn.execute("SELECT MAX(s.sid) from seller as s")
      sid_max = int(list(cursor.first())[0])
      sid = sid_max + 1
    
    

  cmd = 'INSERT INTO products_post_has VALUES (:pid, :sid, :iid, :pname, :price, :number, :customized_description)';
  
  g.conn.execute(text(cmd), pid=new_pid, sid=str(sid), iid=new_iid, pname=name, price=price, number=number, customized_description=customized_description);
  print "sucessful"
#   except:
#     return page_not_found('Unsuccessful insert')


  return redirect('/stuff')

# Example of adding new data to the database
# @app.route('/add', methods=['POST'])
# def add():
#   name = request.form['name']
#   print name
#   cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
#   g.conn.execute(text(cmd), name1 = name, name2 = name);
#   return redirect('/')


# @app.route('/login')
# def login():
#     abort(401)
#     this_is_never_executed()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error = e), 404

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
