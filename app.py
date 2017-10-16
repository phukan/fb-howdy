#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os
import pymongo
import random
import time
from googleapiclient.discovery import build

from flask import Flask
from flask import request
from flask import make_response
from os import environ
app_key=environ.get('google_search_api_key')
cse_id=environ.get('cse_id')

# Flask app should start in global layout
app = Flask(__name__)


uri = environ.get('mongo_url')
client = pymongo.MongoClient(uri)
db = client.get_default_database()
cursor = db.product.find({'product_id': {'$gt': 1}})
wine_items=[]
#user_name=request.get("originalRequest").get("data").get("user").get("name")
total_price=0




@app.route('/webhook', methods=['POST'])
def webhook():
	req = request.get_json(silent=True, force=True)

	print("Request:")
	print(json.dumps(req, indent=4))

	res = processRequest(req)

	res = json.dumps(res, indent=4)
	# print(res)
	r = make_response(res)
	r.headers['Content-Type'] = 'application/json'
	return r

def getUserName(req):
	try:
		user_name = req.get("originalRequest").get("data").get("user").get("name")
		print ('user name',user_name)
		return user_name
	except:
		print (user_name,'error')
		return ""
	
def product_find(cat_id):
	cur=db.product.find( {"category_id": cat_id})
	data=[]
	button_name=['Locate','Call for Assistance','Add to Cart']
	for item in cur:
		tmp_dict = {}
		buttons = []
		product_name=item['name']
		image_url=item['image_url']
		images=[{"url":image_url}]
		price=item['price']
		for i in button_name:
			button = {"type": "imBack", "title":i, "value":i+" "+product_name}
			buttons.append(button)
		tmp_dict["content"] = {"images": images, "buttons": buttons, "title": product_name+" "+price}
		tmp_dict["contentType"] = "application/vnd.microsoft.card.hero"
		data.append(tmp_dict)
		
	return {
		"speech": "",
		"displayText": "",
		# "data": data,
		# "contextOut": [],
		"contextOut": [
        	{
            		"name": "testcontext",
            		"lifespan": 5,
            		"parameters": {
            			"test": "test"
        			}
    		}
    		],
    		"messages": [
        		{
        			"type": 0,
				"platform": "skype",
            			"speech": "Please select an option"				
        		},
        		{
            			"type": 4,
            			"platform": "skype",
            			"speech": "",
            			"payload": {
                		"skype": {
                		"attachmentLayout": "carousel",
                		"attachments": data
				

               		 }
            	}
        	}
    	],
		"source": "webhookdata"
	}

	

def processRequest(req):
					
	if req.get("result").get("action") == "yahooWeatherForecast":
		baseurl = "https://query.yahooapis.com/v1/public/yql?"
		yql_query = makeYqlQuery(req)
		if yql_query is None:
			return {}
		yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
		result = urlopen(yql_url).read()
		data = json.loads(result)
		res = makeWebhookResult(data)
	elif req.get("result").get("action") == "getAtomicNumber":
		data = req
		res = makeWebhookResultForGetAtomicNumber(data)
	elif req.get("result").get("action") == "getChemicalSymbol":
		data = req
		res = makeWebhookResultForGetChemicalSymbol(data)
	elif req.get("result").get("action") == "WineByTaste":
		data = req
		res = makeWebhookResultForWineByTaste(data)
	elif req.get("result").get("action") == "AddToCart":
		data = req
		res = makeWebhookResultForGetWineProduct(data)		
	elif req.get("result").get("action") == "ViewCart":
		data = req
		res = makeWebhookResultForViewProduct(data)
	elif req.get("result").get("action") == "WineWithMealFood":
		data = req
		res = makeWineWithMealFood(data)
	elif req.get("result").get("action") == "BuyItem":
		data = req
		res = makeBuyItem(data)
	elif req.get("result").get("action") == "RemoveCart":
		data = req
		res = makeWebhookResultForRemoveCart(data)
	elif req.get("result").get("action") == "AddToWishlist":
		data = req
		res = makeWebhookResultAddToWishlist(data)
	elif req.get("result").get("action") == "ViewWishlist":
		data = req
		res = makeWebhookResultForViewWishlist(data)
	elif req.get("result").get("action") == "FinalBuy":
		data = req
		res = makeWebhookResultForFinalBuy(data)
	elif req.get("result").get("action") == "ModifyCart":
		data = req
		res = makeWebhookResultModifyCart(data)
	elif req.get("result").get("action") == "broffer":
		data = req
		res = makeWebhookResultbroffer(data)
	elif req.get("result").get("action") == "mealoffer":
		data = req
		res = makeWebhookResultmealoffer(data)
	elif req.get("result").get("action") == "seafoodoffer":
		data = req
		res = makeWebhookResultseafoodoffer(data)
	elif req.get("result").get("action") == "produceoffer":
		data = req
		res = makeWebhookResultproduceoffer(data)
	elif req.get("result").get("action") == "SoupsCannedoffer":
		data = req
		res = makeWebhookResultSoupsCannedoffer(data)
	elif req.get("result").get("action") == "BrowseAisles":
		data = req
		res = makeWebhookResultBrowseAisles(data)
	elif req.get("result").get("action") == "LocateItemCatDetail":
		data = req
		res = makeWebhookResultLocateItemDetail(data)
	elif req.get("result").get("action") == "LocateProduct":
		data = req
		res = makeWebhookResultLocateProduct(data)
	elif req.get("result").get("action") == "lastorder":
		data = req
		res = makeWebhookResultlastorder(data)
	elif req.get("result").get("action") == "ord_detail":
		data = req
		res = makeWebhookResultorddetail(data)
	elif req.get("result").get("action") == "unknown":
		data = req
		res = makeWebhookFallback(data)
	else:
		return {}
	return res

def makeWebhookResultForGetChemicalSymbol(data):
	element = data.get("result").get("parameters").get("elementname")
	chemicalSymbol = 'Unknown'
	if element == 'Carbon':
		chemicalSymbol = 'C'
	elif element == 'Hydrogen':
		chemicalSymbol = 'H'
	elif element == 'Nitrogen':
		chemicalSymbol = 'N'
	elif element == 'Oxygen':
		chemicalSymbol = 'O'
	speech = 'The Chemical symbol of '+element+' is '+chemicalSymbol
	
	return {
		"speech": speech,
		"displayText": speech,
		"source": "webhookdata"
	}

def makeWebhookResultForGetWineProduct(data):
	user_name=getUserName(data)	
	quantity = data.get("result").get("parameters").get("Quantity")
	item = data.get("result").get("parameters").get("wine_product")
	result = db.add_to_cart.find({"user_name":user_name,"product_name":item})
	prod_price=db.product.find({"name":item},{"price":1,"image_url":1,"_id":0})
	for prod in prod_price:
		price=str('$')+str(round(float(str(prod['price'])[1:]),2))
		print(price)
		image=prod['image_url']
	if result.count()==0:
		db.add_to_cart.insert({"user_name":user_name,"product_name":item,"Quantity":quantity,"price":price,"image_url":image})
	data=[]
	total=0
	button_name=['Delete']
	for item in db.add_to_cart.find({"user_name":user_name}):
		total=total + round((float(str(item['price'])[1:])*int(item['Quantity'])),2)
		total=round(total,2)
		print(total)
		tmp_dict={}
		buttons=[]
		product_name=item['product_name']
		quantity=item['Quantity']
		price=str('$')+str(round(float(str(item['price'])[1:])*int(item['Quantity']),2))
		print("price"+price)
		for i in button_name:
			button = {"type": "imBack", "title":i, "value":i+" "+product_name}
			buttons.append(button)
		tmp_dict["content"] = {"buttons": buttons, "title": product_name,"subtitle":"Quantity : "+quantity+" Price : "+price}
		tmp_dict["contentType"] = "application/vnd.microsoft.card.hero"
		data.append(tmp_dict)
	data1=[]
	button_confirm=["Confirm Order"]
	tmp1_dict={}
	buttons1=[]
	for j in button_confirm:
		button = {"type": "imBack", "title":j, "value":j}
		buttons1.append(button)
	tmp1_dict["content"] = {"buttons": buttons1, "title":"     Grand Total : " + str("$")+str(total) }
	tmp1_dict["contentType"] = "application/vnd.microsoft.card.hero"
	data1.append(tmp1_dict)	
	return {
		"speech": "",
		"displayText": "",
		# "data": data,
		# "contextOut": [],
		"contextOut": [
        	{
            		"name": "testcontext",
            		"lifespan": 5,
            		"parameters": {
            			"test": "test"
        			}
    		}
    		],
    		"messages": [
        		{
        			"type": 0,				
            			"speech": "Checking payload message"
        		},
        		{
            			"type": 0,
            			"platform": "skype",
            			"speech": "To view your cart at anytime - Type <b>'Show Cart'</b>"
        		},
			{
            			"type": 0,
            			"platform": "skype",
            			"speech": "<b>========My Cart=========</b>"
        		},
        		{
            			"type": 4,
            			"platform": "skype",
            			"speech": "",
            			"payload": {
                		"skype": {
				"attachmentLayout": "carousel",
                		"attachments": data
               		 }
			}
			},
			 {
            			"type": 4,
            			"platform": "skype",
            			"speech": "",
            			"payload": {
                		"skype": {
                		"attachmentLayout": "list",
                		"attachments": data1
               		 }
            	}
        	}
    	],
		"source": "webhookdata"
	}
	
	

def makeWebhookResultForViewProduct(data):
	user_name=getUserName(data)
	total=0
	result = db.add_to_cart.find({"user_name":user_name})
	if result.count()==0:
		data1=[]
		button_confirm=["Continue Shopping"]
		tmp1_dict={}
		buttons1=[]
		for j in button_confirm:
			button = {"type": "imBack", "title":j, "value":j}
			buttons1.append(button)
		tmp1_dict["content"] = {"buttons": buttons1,"title":"         Your Cart is empty"}
		tmp1_dict["contentType"] = "application/vnd.microsoft.card.hero"
		data1.append(tmp1_dict)
		return {
		"speech": "",
		"displayText": "",
		# "data": data,
		# "contextOut": [],
		"contextOut": [
        	{
            		"name": "testcontext",
            		"lifespan": 5,
            		"parameters": {
            			"test": "test"
        			}
    		}
    		],
    		"messages": [
        		{
        			"type": 0,
            			"speech": "Checking payload message"
        		},
        		{
            			"type": 4,
            			"platform": "skype",
            			"speech": "",
            			"payload": {
                		"skype": {
                		"attachmentLayout": "list",
                		"attachments": data1
               		 }
            	}
        	}
			],
		"source": "webhookdata"
		}
	
	else:
		data=[]
		button_name=['Delete']
		#prod_list=[]
		for item in result:
			total=total + float(str(item['price'])[1:])*int(item['Quantity'])
			tmp_dict={}
			buttons=[]
		#speech = 'My Cart :'
			product_name=item['product_name']
			quantity=item['Quantity']
			price=str('$')+str(float(str(item['price'])[1:])*int(item['Quantity']))
			for i in button_name:
				button = {"type": "imBack", "title":i, "value":i+" "+product_name}
				buttons.append(button)
			tmp_dict["content"] = {"buttons": buttons, "title": product_name,"subtitle":"Quantity : "+quantity+" Price : "+price}
			tmp_dict["contentType"] = "application/vnd.microsoft.card.hero"
			data.append(tmp_dict)
		data1=[]
		print(total)
		button_confirm=["Confirm Order"]
		tmp1_dict={}
		buttons1=[]
		for j in button_confirm:
			button = {"type": "imBack", "title":j, "value":j}
			buttons1.append(button)
		tmp1_dict["content"] = {"buttons": buttons1, "title":"     Grand Total : " + str("$")+str(total) }
		tmp1_dict["contentType"] = "application/vnd.microsoft.card.hero"
		data1.append(tmp1_dict)		
		print(data1)
	
	return {
		"speech": "",
		"displayText": "",
		# "data": data,
		# "contextOut": [],
		"contextOut": [
        	{
            		"name": "testcontext",
            		"lifespan": 5,
            		"parameters": {
            			"test": "test"
        			}
    		}
    		],
    		"messages": [
        		{
        			"type": 0,
            			"speech": "Checking payload message"
        		},
        		{
            			"type": 0,
            			"platform": "skype",
            			"speech": "<b>=========My Cart==========</b>"
        		},
        		{
            			"type": 4,
            			"platform": "skype",
            			"speech": "",
            			"payload": {
                		"skype": {
                		"attachmentLayout": "carousel",
                		"attachments": data
               		 }
			}
			},
			 {
            			"type": 4,
            			"platform": "skype",
            			"speech": "",
            			"payload": {
                		"skype": {
                		"attachmentLayout": "list",
                		"attachments": data1
               		 }
            	}
        	}
    	],
		"source": "webhookdata"
	}

def makeWineWithMealFood(data):
	food_item = data.get("result").get("parameters").get("Food_Item")
	food_item="".join(str(x) for x in food_item)
	food = db.product.find({"name":food_item},{"product_id":1,"_id":0})
	if food.count()==0:
		cur=db.product.find( { "product_id" : { "$in": [1001, 1002, 1069, 1070] }})
	else:
		for item in food:
			food_item_id=int(item['product_id'])
		food_wine=db.product_map.find({"product_id_food":food_item_id},{"product_id_wine":1,"_id":0})
		for item in food_wine:
			food_wine_id=str(item['product_id_wine']).split(",")
		food_wine_id = list(map(int,food_wine_id))
		print(food_wine_id)
		cur=db.product.find( { "product_id" : { "$in": food_wine_id }})
	data=[]
		#cur1=db.product.count( { "product_id" : { "$in": food_wine_id }})
	button_name=['Locate','Call for Assistance','Add to Cart']
	for item in cur:
		tmp_dict = {}
		buttons = []
		product_name=item['name']
		image_url=item['image_url']
		images=[{"url":image_url}]
		price=item['price']
		for i in button_name:
			button = {"type": "imBack", "title":i, "value":i+" "+product_name}
			buttons.append(button)
		tmp_dict["content"] = {"images": images, "buttons": buttons, "title": product_name+" "+price}
		tmp_dict["contentType"] = "application/vnd.microsoft.card.hero"
		data.append(tmp_dict)
		
	return {
		"speech": "",
		"displayText": "",
		# "data": data,
		# "contextOut": [],
		"contextOut": [
        	{
            		"name": "testcontext",
            		"lifespan": 5,
            		"parameters": {
            			"test": "test"
        			}
    		}
    		],
    		"messages": [
        		{
        			"type": 0,
            			"speech": "Checking payload message"
        		},
        		{
            			"type": 0,
            			"platform": "skype",
            			"speech": "Please find the wines matching with  "+food_item
        		},
        		{
            			"type": 4,
            			"platform": "skype",
            			"speech": "",
            			"payload": {
                		"skype": {
                		"attachmentLayout": "carousel",
                		"attachments": data
				

               		 }
            	}
        	}
    	],
		"source": "webhookdata"
	}

def makeWebhookResultLocateItemDetail(data):
	cat_name = data.get("result").get("parameters").get("category")
	loc_detail = db.category.find({"category_name":cat_name},{"location":1,"_id":0})
	#print(cat_name)
	#speech = 'Location of '+cat_name+' is :'
	data=[]
	for row in loc_detail:
		tmp_dict = {}
		location = row['location']
		images=[{"url":"http://noecommercews1098.cloudapp.net/content/images/thumbs/0000201_store-map_415.jpeg"}]
		tmp_dict["content"] = {"images": images,"title": "location of "+cat_name +" is :"+location}
		tmp_dict["contentType"] = "application/vnd.microsoft.card.hero"
		data.append(tmp_dict)
	
	return {
		"speech": "",
		"displayText": "",
		# "data": data,
		# "contextOut": [],
		"contextOut": [
        	{
            		"name": "testcontext",
            		"lifespan": 5,
            		"parameters": {
            			"test": "test"
        			}
    		}
    		],
    		"messages": [
        		{
        			"type": 0,
            			"speech": "Checking payload message"
        		},
        		{
            			"type": 4,
            			"platform": "skype",
            			"speech": "",
            			"payload": {
                		"skype": {
                		"attachmentLayout": "list",
                		"attachments": data
               		 }
            	}
        	}
			],
		"source": "webhookdata"
		}

def makeWebhookResultLocateProduct(data):
	prod_name = data.get("result").get("parameters").get("wine_product")
	cat = db.product.find({"name":prod_name},{"category_id":1,"_id":0})
	for item in cat:
		cat_item_id=int(item['category_id'])
	print(cat_item_id)
	cat_loc=db.category.find({"category_id":cat_item_id},{"location":1,"_id":0})
	#speech = 'Location of '+prod_name+' is :'
	data=[]
	for loc in cat_loc:
		tmp_dict = {}
		location =loc['location']
		images=[{"url":"http://noecommercews1098.cloudapp.net/content/images/thumbs/0000201_store-map_415.jpeg"}]
		tmp_dict["content"] = {"images": images,"title": "location of "+prod_name +" is :"+location}
		tmp_dict["contentType"] = "application/vnd.microsoft.card.hero"
		data.append(tmp_dict)
	return {
		"speech": "",
		"displayText": "",
		# "data": data,
		# "contextOut": [],
		"contextOut": [
        	{
            		"name": "testcontext",
            		"lifespan": 5,
            		"parameters": {
            			"test": "test"
        			}
    		}
    		],
    		"messages": [
        		{
        			"type": 0,
            			"speech": "Checking payload message"
        		},
        		{
            			"type": 4,
            			"platform": "skype",
            			"speech": "",
            			"payload": {
                		"skype": {
                		"attachmentLayout": "list",
                		"attachments": data
               		 }
            	}
        	}
			],
		"source": "webhookdata"
		}
def makeBuyItem(data):
	user_name=getUserName(data)
	cur=db.add_to_cart.find({"user_name":user_name},{"_id":0})
	#order_id=random.randint(10000,20000)
	#print ("order id ", order_id)
	print ("user name again ", user_name)
	#purchase_time=time.strftime("%d/%m/%Y-%H:%M:%S")
	total=0
	order_cur=db.order.find({"user_name":user_name},{"_id":0})
	#for item in cur:
	#	db.order.insert({"order_id":order_i"user_name":item['user_name'],"product_name":item['product_name'],"price":item['price'],"Quantity":item['Quantity'],"Purchase_Time":purchase_time})
	speech = 'Thank You for Your order' + '\n'
	
	#speech = ' Your Order Number : ' + str(order_id) + ' with order detail '
	for row in db.add_to_cart.find({'user_name':user_name}):
		total=total + round(float(str(row['price'])[1:]),2)*int(row['Quantity'])
		speech = speech + '\n' + row['product_name'] + ',  Quantity - ' + row['Quantity'] + ', Total Price - ' + str('$')+str(round(float(str(row['price'])[1:])*int(row['Quantity']),2)) + '\n'
	speech = speech + '\n' + 'Grand Total : ' + str('$')+str(total) + '\n' 	
	speech = speech + '\n' + 'Order will be dlivered to your default delivery address within 2 hours'+'\n'		
	speech = speech + '\n' + 'To securely complete your purchase, reply with the unique "BUYCODE (eg: BUY1818)"' + '\n'
	
	return {
		"speech": speech,
		"displayText": speech,
		"source": "webhookdata"
	}

def makeWebhookResultForFinalBuy(data):
	user_name=getUserName(data)
	order_id=random.randint(10000,20000)
	#order_cur=db.order.find({"user_name":user_name},{"_id":0})
	cur=db.add_to_cart.find({"user_name":user_name},{"_id":0})
	purchase_time=time.strftime("%d/%m/%Y-%H:%M:%S")
	for item in cur:
		db.order.insert({"order_id":order_id,"user_name":item['user_name'],"product_name":item['product_name'],"price":item['price'],"Quantity":item['Quantity'],"Purchase_Time":purchase_time})
	
	speech = 'You are Done! Your Order id is : ' + str(order_id) + '\n'
	speech = speech + 'You can use the order id to track your order as well' + '\n'
	db.add_to_cart.remove({"user_name":user_name})	
	
	return {
		"speech": speech,
		"displayText": speech,
		"source": "webhookdata"
	}
def makeWebhookResultAddToWishlist(data):
	user_name=getUserName(data)	
	wine_item = data.get("result").get("parameters").get("wine_product")
	result = db.wishlist.find({"user_name":user_name,"product_name":wine_item})
	if result.count()==0:
		db.wishlist.insert({"user_name":user_name,"product_name":wine_item})
	speech = 'Items in Your Wishlist are :'
	for row in db.wishlist.find({'user_name':user_name}):
		speech = speech + '\n' + 'Product Name : ' + row['product_name'] + '\n' 
	
	return {
		"speech": speech,
		"displayText": speech,
		"source": "webhookdata"
	}

def makeWebhookFallback(data):
	search_pattern=data.get("result").get("resolvedQuery")
	#print(search_pattern)
	#new=2
	#tabUrl="http://google.com/?#q=";
	speech='The subject you typed is irrelevant to me. Please find the search result in google for ' +search_pattern
	
	def google_search(search_term, api_key, cse_id, **kwargs):
		service = build("customsearch", "v1", developerKey=api_key)
		res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
		return res['items']
	results = google_search(search_pattern,app_key, cse_id, num=1)
	speech=speech + "\n" + results[0]['link']
	#speech = speech + "\n" + contents
	#print(speech)
	
	return {
		"speech": speech,
		"displayText": speech,
		"source": "webhookdata"
	}
	
def makeWebhookResultForViewWishlist(data):
	user_name=getUserName(data)
	result = db.wishlist.find({"user_name":user_name})
	
	if result.count()==0:
		speech="No Item in your Wishlist"
	else:
		speech = 'Items in Your Wishlist are :'
		for row in db.wishlist.find({'user_name':user_name}):
			speech = speech + '\n' + 'Product Name : '+ row['product_name'] + '\n'
	return {
		"speech": speech,
		"displayText": speech,
		"source": "webhookdata"
	}

	
def makeWebhookResultlastorder(data):
	user_name=getUserName(data)
	cur=db.order.find({"user_name":user_name}).sort("Purchase_Time",1)
	total=0
	for item in cur:
		ord_id=item['order_id']
	speech = 'Hello '+user_name+'!!'+' Your Last Order Number : ' + str(ord_id) + '\n'
	for row in db.order.find({'user_name':user_name,'order_id':ord_id}):
		total=total + round(float(str(row['price'])[1:]),2)*int(row['Quantity'])
		speech = speech + '\n' + row['product_name'] + ',  Quantity - ' + row['Quantity'] + ', Total Price - ' + str('$')+str(round(float(str(row['price'])[1:])*int(row['Quantity']),2)) + '\n'
	speech = speech + '\n' + 'Grand Total : ' + str('$')+str(total) + '\n' 
	
	speech = speech + '\n' + 'Order will be dlivered to your default delivery address within 2 hours'+'\n'	
	
	return {
		"speech": speech,
		"displayText": speech,
		"source": "webhookdata"
	}
		
def makeWebhookResultorddetail(data):
	user_name=getUserName(data)
	ord_id = data.get("result").get("parameters").get("number")
	ord_id=int(ord_id)
	print(type(ord_id))
	print(ord_id)
	
	total=0
	result=db.order.find({'user_name':user_name,'order_id':ord_id})
	if result.count()==0:
		speech ='Please enter correct Order Number'
	else:
		speech='Hello '+user_name+'!!'+'Your Last Order Number : ' + str(ord_id) + '\n'
		for row in result:
			total=total + round(float(str(row['price'])[1:]),2)*int(row['Quantity'])
			print(total)
			print(row['product_name'])
			print(row['Quantity'])
			speech = speech + '\n' + row['product_name'] + ',  Quantity - ' + row['Quantity'] + ', Total Price - ' + str('$')+str(round(float(str(row['price'])[1:])*int(row['Quantity']),2)) + '\n'
			print(speech)
		speech = speech + '\n' + 'Grand Total : ' + str('$')+str(total) + '\n' 
		speech = speech + '\n' + 'Order will be dlivered to your default delivery address within 2 hours'+'\n'	
	
	return {
		"speech": speech,
		"displayText": speech,
		"source": "webhookdata"
	}
	

def makeWebhookResultForRemoveCart(data):
	user_name=getUserName(data)
	print ("Chekcing user name "+user_name)
	#cart=db.add_to_cart.remove({"user_name":user_name})
	#print (str(cart.n) + ' items removed from the cart')
	#speech = str(cart.n) + ' items removed from the cart'
	if db.add_to_cart.remove({"user_name":user_name}):
		speech = "Cart items are removed successfully."
	else:
		speech = "Items not properly removed from the cart" 

	return {
		"speech": speech,
		"displayText": speech,
		"source": "webhookdata"
	}

def makeWebhookResultModifyCart(data):
	user_name=getUserName(data)
	item = data.get("result").get("parameters").get("wine_product")
	db.add_to_cart.remove( { "product_name": item } )
	data1=[]
	button_confirm=["Continue Shopping","Show Cart"]
	tmp1_dict={}
	buttons1=[]
	for j in button_confirm:
		button = {"type": "imBack", "title":j, "value":j}
		buttons1.append(button)
	tmp1_dict["content"] = {"buttons": buttons1,"title":"Item Successfully removed from your cart"}
	tmp1_dict["contentType"] = "application/vnd.microsoft.card.hero"
	data1.append(tmp1_dict)
	return {
		"speech": "",
		"displayText": "",
		# "data": data,
		# "contextOut": [],
		"contextOut": [
        	{
            		"name": "testcontext",
            		"lifespan": 5,
            		"parameters": {
            			"test": "test"
        			}
    		}
    		],
    		"messages": [
        		{
        			"type": 0,
            			"speech": "Checking payload message"
        		},
        		{
            			"type": 4,
            			"platform": "skype",
            			"speech": "",
            			"payload": {
                		"skype": {
                		"attachmentLayout": "list",
                		"attachments": data1
               		 }
            	}
        	}
			],
		"source": "webhookdata"
		}

def makeWebhookResultbroffer(data):
	return product_find(200)

def makeWebhookResultmealoffer(data):
	return product_find(300)

def makeWebhookResultproduceoffer(data):
	return product_find(400)

def makeWebhookResultseafoodoffer(data):
	return product_find(500)

def makeWebhookResultSoupsCannedoffer(data):
	return product_find(600)


def makeWebhookResultBrowseAisles(data):
	cat_id=[200,300,400,500,600]
	cur=db.category.find( { "category_id" : { "$in": cat_id }})
	data=[]
	for item in cur:
		tmp_dict = {}
		buttons = []
		category_name=item['category_name']
		print(category_name)
		image_url=item['image_url']
		images=[{"url":image_url}]
		button = {"type": "imBack", "title":"Show Item", "value":"Show Item"+" "+category_name}
		buttons.append(button)
		tmp_dict["content"] = {"images": images, "buttons": buttons, "title": category_name}
		tmp_dict["contentType"] = "application/vnd.microsoft.card.hero"
		data.append(tmp_dict)
	print(data)
		
		
	return {
		"speech": "",
		"displayText": "",
		# "data": data,
		# "contextOut": [],
		"contextOut": [
        	{
            		"name": "testcontext",
            		"lifespan": 5,
            		"parameters": {
            			"test": "test"
        			}
    		}
    		],
    		"messages": [
        		{
        			"type": 0,
				"platform": "skype",
            			"speech": "Please select an option"				
        		},
        		{
            			"type": 4,
            			"platform": "skype",
            			"speech": "",
            			"payload": {
                		"skype": {
                		"attachmentLayout": "carousel",
                		"attachments": data				

               		 }
            	}
        	}
    	],
		"source": "webhookdata"
	}



	
def makeWebhookResultForWineByTaste(data):
	
	# mongo db result
	for doc in cursor:
		dbRes1, dbRes2 = doc['product_id'], doc['name']
		
	col = data.get("result").get("parameters").get("color")
	st_of_col = data.get("result").get("parameters").get("style_of_color")
	WineTaste = 'Unknown'
	if col == 'Pink(Rose/Blush)' and st_of_col =='Light & Bubbly':
		WineTaste = "Sparkling Wine (Rose)\
			A crisp, sparkling blush wine with flavours of red berries\
			Highly rated wines\
			Domaine Carneros Brut Rose Cuvee de la Pompadour Sparkling wine (Rose)\
			Sipping Point Picks\
			Jacob’s Creek Rose Moscato Sparkling Wine Banfi Rosa Regale Sparkling Red Brachetto\
			Value $10 & under\
			Cook’s Sparkling Wine (Rose)"
	elif col == 'Red' and st_of_col =='Dry & Fruity':
		WineTaste = '''
		{
 "speech": "Alright! 30 min sounds like enough time!",
  "messages": [
    {
      "type": 4,
      "platform": "skype",
      "payload": {
        "skype": {
          "type": "message",
          "attachmentLayout": "list",
          "text": "",
          "attachments": [
            {
              "contentType": "application\/vnd.microsoft.card.hero",
              "content": {
                "title": "Unit 2A Availibity",
                "subtitle": "Max Participants 12",
                "text": "",
                "buttons": [
                  {
                    "type": "imBack",
                    "title": "08:00:00\/09:00:00",
                    "value": "08:00:00\/09:00:00"
                  },
                  {
                    "type": "imBack",
                    "title": "09:30:00\/18:00:00",
                    "value": "09:30:00\/18:00:00"
                  }
                ]
              }
            }
          ]
        }
      }
    }
  ]
}
		'''
	elif col == 'White' and st_of_col =='Sweet':
		WineTaste = str(dbRes1) + str(dbRes2)
	elif col == 'White' and st_of_col =='Semi-sweet':
		WineTaste = 'O'
	speech = WineTaste
	skype_message = {
  				"skype": {
    				"data": WineTaste
  				}
			}
	
	return {
		"speech": speech,
		"displayText": speech,
		"data": {"skype": {skype_message}},
		"source": "webhookdata",
		}
		
def makeWebhookResultForGetAtomicNumber(data):
	element = data.get("result").get("parameters").get("elementname")
	atomicNumber = 'Unknown'
	if element == 'Carbon':
		atomicNumber = '6'
	elif element == 'Hydrogen':
		atomicNumber = '1'
	elif element == 'Nitrogen':
		atomicNumber = '7'
	elif element == 'Oxygen':
		atomicNumber = '8'
	speech = 'The atomic number of '+element+' is '+atomicNumber
	
	return {
		"speech": speech,
		"displayText": speech,
		"source": "webhookdata"
	}
	

def makeYqlQuery(req):
	result = req.get("result")
	parameters = result.get("parameters")
	city = parameters.get("geo-city")
	if city is None:
		return None

	return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"


def makeWebhookResult(data):
	query = data.get('query')
	if query is None:
		return {}

	result = query.get('results')
	if result is None:
		return {}

	channel = result.get('channel')
	if channel is None:
		return {}

	item = channel.get('item')
	location = channel.get('location')
	units = channel.get('units')
	if (location is None) or (item is None) or (units is None):
		return {}

	condition = item.get('condition')
	if condition is None:
		return {}

	# print(json.dumps(item, indent=4))

	speech = "Today in " + location.get('city') + ": " + condition.get('text') + \
			 ", the temperature is " + condition.get('temp') + " " + units.get('temperature')

	print("Response:")
	print(speech)

	return {
		"speech": "",
		"displayText": "",
		# "data": data,
		# "contextOut": [],
		"contextOut": [
            {
                "name": "testcontext",
                "lifespan": 5,
                "parameters": {
                	"test": "test"
            	}
        	}
        ],
        "messages": [
            {
            	"type": 0,
                "speech": "Checking payload message"
            },
            {
                "type": 0,
                "platform": "skype",
                "speech": "test message"
            },
            {
                "type": 4,
                "platform": "skype",
                "speech": "",
                "payload": {
                    "skype": {
                    "attachmentLayout": "carousel",
                    "attachments": [
      {
        "contentType": "application/vnd.microsoft.card.hero",
        "content": {
          "title": "Bisquick Baking & Pancake Mix",
          "subtitle": "20% Discount - $4.49",
          "images": [
            {
              "url": "http://noecommercews1098.cloudapp.net/content/images/thumbs/0000118_bisquick-baking-pancake-mix_415.jpeg"
            }
          ],
          "buttons": [
            {
              "type": "imBack",
              "title": "Locate",
              "value": "Locate"
            },
            {
              "type": "imBack",
              "title": "Call for Assistance",
              "value": "Call for Assistance"
            },
            {
              "type": "imBack",
              "title": "Add to Cart",
              "value": "Add to Cart Bisquick Baking & Pancake Mix"
            }
          ]
        }
      },
      {
        "contentType": "application/vnd.microsoft.card.hero",
        "content": {
          "title": "General Mills Cheerios Cereal Gluten Free",
          "subtitle": "15% Discount - $3.29",
          "images": [
            {
              "url": "http://noecommercews1098.cloudapp.net/content/images/thumbs/0000108_general-mills-cheerios-cereal-gluten-free_415.jpeg"
            }
          ],
          "buttons": [
            {
              "type": "imBack",
              "title": "Locate",
              "value": "Locate"
            },
            {
              "type": "imBack",
              "title": "Call for Assistance",
              "value": "Call for Assistance"
            },
            {
              "type": "imBack",
              "title": "Add to Cart",
              "value": "Add to Cart General Mills Cheerios Cereal Gluten Free"
            }
          ]
        }
      },
      {
        "contentType": "application/vnd.microsoft.card.hero",
        "content": {
          "title": "Kellogg's Frosted Flakes Cereal",
          "subtitle": "15% Discount - $2.50",
          "images": [
            {
              "url": "http://noecommercews1098.cloudapp.net/content/images/thumbs/0000114_kelloggs-frosted-flakes-cereal_415.jpeg"
            }
          ],
          "buttons": [
            {
              "type": "imBack",
              "title": "Locate",
              "value": "Locate"
            },
            {
              "type": "imBack",
              "title": "Call for Assistance",
              "value": "Call for Assistance"
            },
            {
              "type": "imBack",
              "title": "Add to Cart",
              "value": "Add to Cart Kellogg's Frosted Flakes Cereal"
            }
          ]
        }
      }
    ]

                    }
                }
            }
        ],
		"source": "apiai-weather-webhook-sample"
	}


if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))

	print("Starting app on port %d" % port)

	app.run(debug=False, port=port, host='0.0.0.0')
