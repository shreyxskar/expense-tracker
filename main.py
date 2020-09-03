from flask import Flask, render_template, request, flash, redirect, url_for
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime

app = Flask(__name__)

app.secret_key = 'myExpenseApp'

connection = MongoClient('localhost', 27017)
#database = connection['test_transact_db']
#collection = database['test_collection_02']
database = connection['user_db01']

cat_types = ['Bills', 'Bonus', 'Entertainment', 'Food', 'Health', 'House', 'Salary', 'Transport', 'Extras']

@app.route('/', methods=['GET'])
def index_page():

    global database
    collection = database['expenses']
    present_month = datetime.date.today().month
    upper_bound = str(datetime.date(2020, present_month+1, 1))
    lower_bound = str(datetime.date(2020, present_month, 1))

    res = collection.find({'$and': [{'date': {'$lt': upper_bound}}, {'date': {'$gte': lower_bound}}]})

    
    records = {'total_expenses': 0, 'debit_sum': 0, 'credit_sum': 0}
    for c in cat_types:
        records[c] = 0

    for i in res:
        records['total_expenses'] += 1        
        records[str(i['category'])] += float(i['transaction_amount'])

        if i['credit'] == '-': #debit
            records['debit_sum'] += float(i['transaction_amount'])
        else: #credit
            records['credit_sum'] += float(i['transaction_amount'])
    #print(records)

    return render_template('index_page.html', monthly_records=records)

@app.route('/manage_accounts', methods=['GET', 'POST'])
def manage_accounts():
    global database
    collection = database['accounts']
    if request.method == 'POST':
        acc_name = request.form['acc_name']
        collection.insert_one({'account_name': acc_name, 'date_created': datetime.datetime.now()})
        flash('Account added!')
        return redirect(url_for('manage_accounts'))

    accounts = collection.find()
    return render_template('manage_accounts.html', X=accounts)

@app.route('/add_expense', methods=['GET', 'POST'])
def input_form():
    global cat_types
    global database

    if request.method == "GET":              
        return render_template('input_form.html', cats=cat_types, accounts=database['accounts'].find().distinct('account_name'))
           
    data = {}
    data['transaction_amount'] = request.form['eamount']
    data['date'] = request.form['edate']
    data['description'] = request.form['edescription']
    if request.form['etype'].strip().upper() == 'CREDIT':        
        data['credit'] = request.form['etype']
        data['debit'] = '-'
    else:        
        data['credit'] = '-'
        data['debit'] = request.form['etype']     

    data['category'] = request.form['ecategory'] 
    data['account'] = request.form['eaccount']

    #cc=eamount+edate+edescription+etype
    collection = database['expenses']
    collection.insert_one(data)
    flash('Expense added!')
    #print(cc)
    return render_template('input_form.html', cats=cat_types, accounts=database['accounts'].find().distinct('account_name'))

@app.route('/all_expenses', methods=['GET'])
def all_expenses():
    global database
    collection = database['expenses']    
    return render_template('all_expenses.html', docs_c=collection.find({}).sort('date', -1), accounts=database['accounts'].find().distinct('account_name'))

@app.route('/all_expenses/<account>')
def all_expenses_filter(account):
    global database
    collection = database['expenses']    
    return render_template('all_expenses.html', docs_c=collection.find({'account': account}).sort('date', -1), accounts=database['accounts'].find().distinct('account_name'))

@app.route('/manage_expenses', methods=['GET', 'POST'])
def manage_expenses():  
    global database 
    global cat_types

    collection = database['expenses']
    return render_template('manage_expenses.html', docs_c=collection.find({}), cats=cat_types)


@app.route('/delete_expense/<expense_id>', methods=['POST', 'GET'])
def delete_expense(expense_id):    

    global database
    collection = database['expenses']
    query = {'_id': ObjectId(str(expense_id))}
    collection.delete_one(query)
    flash('Expense Deleted!')
    return redirect(url_for('manage_expenses'))


@app.route('/update_expense', methods=['POST', 'GET'])
def update_expense():
    if request.method == 'GET':
        return redirect(url_for('index_page'))
    
    global database
    collection = database['expenses']
    new_values = {}
    new_values['transaction_amount'] = request.form['ueamount']
    new_values['date'] = request.form['uedate']
    new_values['category'] = request.form['uecategory']
    utype = request.form['uetype']
    if utype.strip().upper() == 'CREDIT':
        new_values['credit'] = 'CREDIT'
        new_values['debit'] = '-'
    else:
        new_values['credit'] = '-'
        new_values['debit'] = 'DEBIT'
    new_values['description'] = request.form['uedescription']
    expense_id = request.form['expense_id'].strip()
    #expense_id = 'ObjectId(\"' + request.form['expense_id'].strip() + '\")'

    collection.update_one({'_id': ObjectId(str(expense_id))}, {"$set": new_values})
    flash('Expense updated!')
    return redirect(url_for('manage_expenses'))


if __name__ == '__main__':
    app.run(debug=True)