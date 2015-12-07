#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

import os, re, time, base64, hashlib, logging,mimetypes
from functools import wraps
from flask import g,Flask,render_template,request,json,jsonify,redirect,url_for,session
from tempfile import mktemp
from shutil import *
from models import Dict,User, Kid, Teacher,Class,I_Class_kids,Attendance,Tuition,I_Tuition,Config,Special_charge,Year_Tuition

app = Flask(__name__)
_RE_MD5 = re.compile(r'^[0-9a-f]{32}$')

from werkzeug.utils import secure_filename

class Page(object):
    '''
    Page object for display pages.
    '''

    def __init__(self, item_count, page_index=1, page_size=6):
        '''
        Init Pagination by item_count, page_index and page_size.
        >>> p1 = Page(100, 1)
        >>> p1.page_count
        10
        >>> p1.offset
        0
        >>> p1.limit
        10
        >>> p2 = Page(90, 9, 10)
        >>> p2.page_count
        9
        >>> p2.offset
        80
        >>> p2.limit
        10
        >>> p3 = Page(91, 10, 10)
        >>> p3.page_count
        10
        >>> p3.offset
        90
        >>> p3.limit
        10
        '''
        self.item_count = item_count
        self.page_size = page_size
        self.page_count = item_count // page_size + (1 if item_count % page_size > 0 else 0)
        if (item_count == 0) or (page_index < 1) or (page_index > self.page_count):
            self.offset = 0
            self.limit = 0
            self.page_index = 1
        else:
            self.page_index = page_index
            self.offset = self.page_size * (page_index - 1)
            self.limit = self.page_size
        self.has_next = self.page_index < self.page_count
        self.has_previous = self.page_index > 1

    def __str__(self):
        return 'item_count: %s, page_count: %s, page_index: %s, page_size: %s, offset: %s, limit: %s' % (self.item_count, self.page_count, self.page_index, self.page_size, self.offset, self.limit)

    __repr__ = __str__
	
def to_dict(page):
    return {'item_count': page.item_count, 'page_count':page.page_count, 'page_index': page.page_index, 'page_size': 'page.page_size', 'offset': page.offset, 'limit': page.limit,'has_next':page.has_next,'has_previous':page.has_previous}		

def _get_page_index():
    page_index = 1
    try:
        page_index = int(request.args.get('page', '1'))
    except ValueError:
        pass
    return page_index


#上传图片#

UPLOAD_FOLDER = 'Static/Photo/uploads/'
ALLOWED_MIMETYPES = {'image/jpeg', 'image/png', 'image/gif'}

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('kid_edit.html', pic_url='')
    elif request.method == 'POST':
        f = request.files['files[]']		
        fname = mktemp(suffix='_', prefix='u', dir=UPLOAD_FOLDER) + secure_filename(f.filename)
        f.save(fname)
        if mimetypes.guess_type(fname)[0] in ALLOWED_MIMETYPES:
            fname=fname.lower()
            return fname
        else:
            os.remove(fname)
            return ''
			
@app.route('/photo', methods=['POST'])
def photo_view():		
    fname = request.data
    fname= str(fname)
    fname = eval(fname).decode('utf-8')
    return fname 


@app.route('/print/tuition',methods=['POST'])
def print_tuition():
    r=request.json    
    printdata=Dict()
    printdata.name=r['kid_name']
    printdata.classname=Class.get(r['k_class']).name
    printdata.cycle=r['month']
    printdata.charges=[]
    if r['tuition']!=0:
        printdata.charges.append({'chargename':r['month']+'应收保教费','charge':r['tuition']})
    if r['foodcosts']!=0:
	    printdata.charges.append({'chargename':r['month']+'应收餐费','charge':r['foodcosts']})
    printdata.chargetotal=r['tuition']+r['foodcosts']
    for special_charge in r['special_charges']:
        printdata.charges.append({'chargename':special_charge['chargename'],'charge':special_charge['charge']})
        printdata.chargetotal=printdata.chargetotal+special_charge['charge']
    printdata.backs=[]
    if r['tuition_back']!=0:
        printdata.backs.append({'backname':r['last_month']+'应退保教费','back':r['tuition_back']})
    if r['foodcosts_back']!=0:
	    printdata.backs.append({'backname':r['last_month']+'应退餐费','back':r['foodcosts_back']})
    printdata.backtotal=r['tuition_back']+r['foodcosts_back']
    printdata.total=printdata.chargetotal-printdata.backtotal
    printdata.remark=r['last_month']+'缺勤'+str(r['absence'])+'天。'
    now=time.localtime(int(time.time()))
    printdata.date=time.strftime("%Y-%m-%d", now)	
    session['printdata']=printdata
    return  jsonify(r='y')
	
@app.route('/print/year_tuition',methods=['POST'])
def print_year_tuition():
    r=request.json 
    printdata=Dict()
    printdata.name=r['kid_name']
    k_class=Kid.get(r['kid_id']).k_class
    if k_class:
        printdata.classname=Class.get(k_class).name    
    printdata.cycle=r['cycle']
    printdata.charges=[]
    printdata.charges.append({'chargename':'保教费','charge':r['charge']})
    printdata.backs=[]
    printdata.chargetotal=r['charge']
    printdata.total=r['charge']
    now=time.localtime(int(time.time()))
    printdata.date=time.strftime("%Y-%m-%d", now)	
    session['printdata']=printdata
    return  jsonify(r='y')
    
@app.route('/print/i_tuition',methods=['POST'])
def print_i_tuition():
    r=request.json    
    printdata=Dict()
    printdata.name=r['kid_name']
    k_class=Kid.get(r['kid_id']).k_class
    if k_class:
        printdata.classname=Class.get(k_class).name
    i_classname=Class.get(r['i_class']).name
    printdata.cycle=r['cycle']
    printdata.charges=[]
    if int(r['charge'])>0:
        printdata.charges.append({'chargename':i_classname+'学费','charge':r['charge']})
        printdata.chargetotal=r['charge']	
    printdata.backs=[]
    if int(r['charge'])<0:
        printdata.backs.append({'backname':i_classname+'学费','back':-r['charge']})
        printdata.backtotal=-r['charge']
    printdata.total=r['charge']
    now=time.localtime(int(time.time()))
    printdata.date=time.strftime("%Y-%m-%d", now)	
    session['printdata']=printdata
    return  jsonify(r='y')
	
@app.route('/print/deposit',methods=['POST'])
def print_deposit():
    r=request.json    
    printdata=Dict()
    printdata.name=r['kid_name']
    k_class=Kid.get(r['kid_id']).k_class
    if k_class:
        printdata.classname=Class.get(k_class).name
    printdata.cycle=r['cycle']
    printdata.charges=[]
    printdata.charges.append({'chargename':'入园押金','charge':r['deposit']})
    printdata.chargetotal=r['deposit']
    printdata.backs=[]   
    printdata.total=printdata.chargetotal
    now=time.localtime(int(time.time()))
    printdata.date=time.strftime("%Y-%m-%d", now)	
    session['printdata']=printdata
    return  jsonify(r='y')
	
@app.route('/print/article',methods=['POST'])
def print_article():
    r=request.json    
    printdata=Dict()
    printdata.name=r['kid_name']
    k_class=Kid.get(r['kid_id']).k_class
    if k_class:
        printdata.classname=Class.get(k_class).name
    printdata.cycle=r['cycle']
    printdata.charges=[]
    if r['article']!=0:
        printdata.charges.append({'chargename':'入园物品费','charge':r['article']})
    if r['bedding']!=0:
	    printdata.charges.append({'chargename':'床品费','charge':r['bedding']})
    if r['test']!=0:
	    printdata.charges.append({'chargename':'体验费','charge':r['test']})
    printdata.chargetotal=r['bedding']+r['article']+r['test']
    printdata.backs=[]   
    printdata.total=printdata.chargetotal
    now=time.localtime(int(time.time()))
    printdata.date=time.strftime("%Y-%m-%d", now)	
    session['printdata']=printdata
    return  jsonify(r='y')	
	
	
@app.route('/print/charge')
def print_charge():
    return render_template('print.html')	
	
@app.route('/api/print/charge')
def api_print_charge():
    r=session['printdata']
    session['printdata']={}
    return jsonify(r=r)		
	
	
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/api/login',methods=['POST'])
def islogin():
    r=request.json
    name = r['user']
    password = r['password']
    remember=r['remember']
    user = User.find_first('where name = ?', name)
    if user:
        if password != user.password:
            is_login='用户不存在或密码错误!'
        else:
            is_login='y'
            session['user']=user.name
            session['admin']=user.admin
            session.permanent = remember
    else:
        is_login='用户不存在或密码错误!'
    return jsonify(is_login=is_login)
	
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'	
	
def authorization(text):   
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kw):
            if 'user' in session:
                if session['admin'].find(text)!=-1:
                    return func(*args, **kw)
                else:
                    return render_template('no_right.html')
            else:		
                return redirect(url_for('login'))         
        return wrapper
    return decorator	
	
	
@app.route('/password')
def password():    
    return render_template('password.html')

@app.route('/api/password')
def api_password():
    name=session['user']
    user=User.find_first('where name=?',name)
    return jsonify(user=user)

@app.route('/api/password/modify',methods=['POST'])
def password_modify():
    r= request.json
    id=r['user']
    user = User.get(id)
    user.password = r['password']    
    user.update()
    return jsonify(user=user)

@app.route('/config')
@authorization('q5_2')
def config_view():
    return render_template('config.html',page_index=_get_page_index())

def _get_charge_by_page():    
    total = Special_charge.count_all()
    page = Page(total, _get_page_index())
    page = to_dict(page)			
    charge =Special_charge.find_by('order by id desc limit ?,?', page['offset'], page['limit'])
    return charge, page
	
@app.route('/api/config')
def config_load():
    config=Config.find_first('where 1 = 1')
    if not config:
        config={}
    charge, page = _get_charge_by_page()
    for i in charge:
	    i.class_name=Class.get(i.class_id).name
    charges=dict(charge=charge,page=page)
    k_classes =Class.find_by('where type=?','常规班')    
    return jsonify(config=config,charges=charges,page=page,k_classes = k_classes)	
	
@app.route('/api/config/edit',methods=['POST'])
def config_edit():
    r=request.json
    config=Config.find_first('where 1 = 1')
    if not config:
        foodcosts=float(r['foodcosts'])
        article=float(r['article'])
        tuition=float(r['tuition'])
        bedding=float(r['bedding'])
        test=float(r['test'])
        discount=float(r['discount'])
        config =Config(kindergarten=r['kindergarten'],month_start=r['month_start'],foodcosts=foodcosts,article=article,tuition=tuition,bedding=bedding,test=test,discount=discount)
        config.insert()
    else:
        config.kindergarten=r['kindergarten']
        config.month_start=r['month_start']
        config.foodcosts=float(r['foodcosts'])
        config.article=float(r['article'])
        config.tuition=float(r['tuition'])
        config.bedding=float(r['bedding'])
        config.test=float(r['test'])
        config.discount=float(r['discount'])
        config.update()
    return jsonify(config)
	
@app.route('/api/special_charge/add',methods=['POST'])
def  special_charge_add_api():
    r=request.json
    chargename = r['chargename']
    month = r['month']
    class_id=r['class_select']
    charge=r['charge']
    charge = Special_charge(chargename=chargename, month=month, class_id=class_id,charge=charge)
    charge.insert()
    return jsonify(charge=charge)	
	
@app.route('/api/special_charge/delete/<id>',methods=['POST'])
def api_delete_special_charge(id):
    charge =Special_charge.get(id)
    charge.delete()
    return jsonify(id=id)		



	
#用户管理模块#

def _get_users_by_page():    
    total = User.count_all()
    page = Page(total, _get_page_index())
    page = to_dict(page)			
    users = User.find_by('order by name desc limit ?,?', page['offset'], page['limit'])
    return users, page
	
@app.route('/users')
@authorization('q5_1')
def users():
    return render_template('user.html', action= '/api/user/add',page_index=_get_page_index())
	
@app.route('/user/edit/<user_id>')  #修改用户页面
@authorization('q5_1')
def user_edit(user_id):
    id = user_id    
    return render_template('user.html',id = id,action='/api/user/edit/%s' % id,page_index=_get_page_index())	


@app.route('/api/users')  
def User_all_load():
    users, page = _get_users_by_page()
    return jsonify(users=users,page=page)
	
@app.route('/api/user/<user_id>')     #单个用户信息信息
def user_one_load(user_id):
    user=User.get(user_id)
    user.password=''
    user.password1 = '******'
    user.password2 = '******'
    return jsonify(user) 

@app.route('/api/user/add',methods=['POST'])
def  user_add_api():
    r=request.json
    name = r['name']
    password = r['password']
    admin=r['admin']
    if not name:
        raise APIValueError('name')
    if not admin:
        raise APIValueError('admin')
    if not password or not _RE_MD5.match(password):
        raise APIValueError('password')
    user = User.find_first('where name=?', name)
    if user:
        raise APIError('register:failed', 'name', 'name is already in use.')
    user = User(name=name, password=password, admin=admin)
    user.insert()
    return jsonify(user=user)
	
@app.route('/api/user/edit/<user>',methods=['POST'])    #修改用户操作
def  user_edit_api(user):
    r= request.json
    user = User.get(user)
    user.name = r['name']
    if (r['password']!='13bbf54a6850c393fb8d1b2b3bba997b'):
        user.password = r['password']    
    user.admin=r['admin']
    user.update()
    return jsonify(user=user)
	
@app.route('/api/user/<user_id>/delete',methods=['POST'])
def api_delete_user(user_id):
    user =User.get(user_id)
    user.delete()
    return jsonify(user_id=user_id)	
	
###################################缴费管理模块########################################		

@app.route('/tuition')     #缴费信息页面#
@authorization('q3_1')
def tuition():
    return render_template('tuition.html',page_index=_get_page_index())
	
@app.route('/tuition/check')     #查询人员缴费页面#
@authorization('')
def tuition_check():
    return render_template('tuition_check.html')	


	
@app.route('/api/tuition/check')     #个人缴费信息# 
def tuition_load():
    k_classes =Class.find_by('where type=?','常规班')
    k_class = request.args.get('class_select')
    start = request.args.get('start')
    end = request.args.get('end')
    name = request.args.get('name')
    kid=Kid.find_first('where name = ?',name)
    if kid and start and end:	
        tuitions=Tuition.find_by('where kid_id=? and time>=? and time<? order by time', kid.id,start,end)
        i_tuitions=I_Tuition.find_by('where kid_id=? and time>=? and time<? order by time', kid.id,start,end)       
        for i_tuition in i_tuitions:
            i_class=Class.find_first('where id=?',i_tuition.class_id)
            i_tuition.chargename=i_class.name+'学费'
            i_tuition.pop('class_id')
            i=0
            for tuition in tuitions:
                if i_tuition.time<tuition.time:
                    tuitions.insert(i, i_tuition)
                    break
                i=i+1
            if i>=len(tuitions):
                tuitions.append(i_tuition)        
    else:
        tuitions=[]
        kid={}    
    return jsonify(kid=kid,tuitions=tuitions,k_classes=k_classes)		
	
@app.route('/api/tuition')     #缴费信息# 
@authorization('q3_1')
def tuitions_load():
    k_classes =Class.find_by('where type=?','常规班')
    k_class = request.args.get('class_select')
    lastmonth_day = request.args.get('lastmonth')
    nowmonth_day = request.args.get('nowmonth')
    ispaid=request.args.get('ispaid')	
    total = Kid.count_by( 'where k_class=?',k_class)
    special_charges=Special_charge.find_by('where class_id=? and month=?',k_class,nowmonth_day)
    kids=[]
    if k_class:
	    kids = Kid.find_by( 'where k_class=?',k_class)
    j=0
    for i in range(len(kids)):
        kids[j].absence=Attendance.count_by('where kid_id=? and day>? and day<? ',kids[j].id,lastmonth_day,nowmonth_day )
        tuitions=Tuition.find_by('where kid_id=? and month=?',kids[j].id,nowmonth_day)
        paid=0
        for tuition in tuitions:
            paid=paid+tuition.paid
        if paid!=0:
            if ispaid=='未交':
                kids.pop(j)
                i=i+1
                j=j-1
                total=total-1				
            else:
                kid_tuition=Tuition.find_first('where kid_id=? and month=? and chargename like ?',kids[j].id,nowmonth_day,'%应收保教费%')
                if kid_tuition:kids[j].tuition=kid_tuition.paid
                else:kids[j].tuition=0
                kid_tuition=Tuition.find_first('where kid_id=? and month=? and chargename like ?',kids[j].id,nowmonth_day,'%应退保教费%')
                if kid_tuition:kids[j].tuition_back=-kid_tuition.paid
                else:kids[j].tuition_back=0				
                kid_tuition=Tuition.find_first('where kid_id=? and month=? and chargename like ?',kids[j].id,nowmonth_day,'%应收餐费%')
                if kid_tuition:kids[j].foodcosts=kid_tuition.paid
                else:kids[j].foodcosts=0				
                kid_tuition=Tuition.find_first('where kid_id=? and month=? and chargename like ?',kids[j].id,nowmonth_day,'%应退餐费%')
                if kid_tuition:kids[j].foodcosts_back=-kid_tuition.paid
                else:kids[j].foodcosts_back=0				
                kids[j].paid=paid
        else:
            if ispaid=='已交':
                kids.pop(j)
                i=i+1
                j=j-1
                total=total-1			
            else:
                kids[j].paid=0

        year_tuition=Year_Tuition.find_first('where kid_id=? and end_month>=? order by end_month desc',kids[j].id,nowmonth_day)
        if year_tuition:
            kids[j].lastmonth=year_tuition.end_month
        j=j+1
    page = Page(total, _get_page_index())
    page = to_dict(page)
    start=page['offset']
    end=page['offset']+page['limit']
    if end > total:
        end=total
    kids=kids[start:end]
    foodcosts=Config.find_first('where 1=1').foodcosts
    return jsonify(kids=kids,k_classes=k_classes,page=page,foodcosts=foodcosts,special_charges=special_charges)	

@app.route('/api/tuition/add',methods=['POST'])    #增加缴费信息操作
@authorization('q3_1')
def  tuition_add_api():
    r= request.json
    kid_id = r['kid_id']
    month = r['month']
    now_month=r['now_month']
    last_month=r['last_month']
    now = int(time.time())
    tuitions = Tuition.find_by('where kid_id=? and month=?',kid_id,month)
    for tuition in tuitions:
        tuition.delete()
    tuition=r['tuition']
    if tuition!=0:
        tuition = Tuition(kid_id=kid_id, time = now,paid= tuition,chargename=now_month+'应收保教费',month=month)
        tuition.insert()
    foodcosts=r['foodcosts']
    if foodcosts!=0:
        tuition = Tuition(kid_id=kid_id, time = now,paid= foodcosts,chargename=now_month+'应收餐费',month=month)
        tuition.insert()
    tuition_back=-r['tuition_back']
    if tuition_back!=0:
        tuition = Tuition(kid_id=kid_id, time = now,paid= tuition_back,chargename=last_month+'应退保教费',month=month)
        tuition.insert()
    foodcosts_back=-r['foodcosts_back']
    if foodcosts_back!=0:
        tuition = Tuition(kid_id=kid_id, time = now,paid= foodcosts_back,chargename=last_month+'应退餐费',month=month)
        tuition.insert()	
    special_charges=r['special_charges']
    for special_charge in special_charges:
        tuition = Tuition(kid_id=kid_id, time = now,chargename = special_charge['chargename'],paid = special_charge['charge'],month=month) 
        tuition.insert()
    return jsonify(tuition=tuition)
	
@app.route('/api/tuition/delete',methods=['POST'])    #删除缴费信息操作
@authorization('q3_1')
def  tuition_delete_api():
    r= request.json
    kid_id = r['kid_id']
    month= r['month']
    tuitions = Tuition.find_by('where kid_id=? and month=?',kid_id,month)
    for tuition in tuitions:
        tuition.delete()
    return jsonify(tuition=tuition)	

@app.route('/year_tuition')     #按年缴纳保教费页面#
@authorization('q3_1')
def year_tuition():
    return render_template('year_tuition.html')	
	
@app.route('/api/year_tuition')    # 按年缴纳保教费信息# 
def year_tuition_load():
    k_classes =Class.find_by('where type=?','常规班')
    class_select = request.args.get('class_select')
    name=request.args.get('name')
    select_order=' where name = '+'\''+name+'\''
    if class_select:
        select_order=select_order+' and k_class = '+'\''+class_select+'\''
    kid = Kid.find_first(select_order)
    if kid:
        tuitions = Tuition.find_first('where kid_id = ? and chargename like ? order by month desc',kid.id,'%应收保教费%')
        tuitions1= Year_Tuition.find_first('where kid_id = ? order by end_month desc',kid.id)
        if tuitions and tuitions1:    
            if tuitions1.end_month>tuitions.month:kid.month=tuitions1.end_month
            else:kid.month=tuitions.month
        if tuitions and (not tuitions1):
            kid.month=tuitions.month
        if (not tuitions) and tuitions1:
            kid.month=tuitions1.end_month
        if not (tuitions or tuitions1):
            kid.month=Kid.find_first('where id = ? ',kid.id).enter_date		
    begindate=Config.find_first('where 1=1').month_start
    discount=Config.find_first('where 1=1').discount
   
    return jsonify(kid=kid,k_classes=k_classes,begindate=begindate,discount=discount)	


@app.route('/api/year_tuition/add',methods=['POST'])    #按年缴纳保教费操作
@authorization('q3_1')
def  year_tuition_add_api():
    r= request.json
    kid_id = r['kid_id']
    now = int(time.time())   
    paid=r['paid']
    start_month=r['start']
    end_month=r['end']
    tuition = Year_Tuition(kid_id=kid_id, time = now,paid = paid,start_month=start_month,end_month=end_month)
    tuition.insert()
    return jsonify(tuition=tuition)
	
@app.route('/year_tuition/check')     #按年缴纳保教费页面#
@authorization('')
def year_tuition_check():
    return render_template('year_tuitions_view.html',page_index=_get_page_index())	
	
@app.route('/api/year_tuition/check')    # 按年缴纳保教费信息查询# 
def api_year_tuition_check():
    k_classes =Class.find_by('where type=?','常规班')
    class_select = request.args.get('class_select')
    name = request.args.get('name')
    select_order='where 1=1 '
    if class_select:
        select_order=select_order+' and k_class = '+'\''+class_select+'\''
    if name:
	    select_order=select_order+' and name like '+'\'%'+name+'%\''   
    kids = Kid.find_by(select_order)
    tuitions=[]
    for kid in kids:
        year_tuitions = Year_Tuition.find_by('where kid_id = ? order by end_month desc',kid.id)        
        for year_tuition in year_tuitions:
            year_tuition.kid_name=kid.name
            year_tuition.kid_id=kid.id
            tuitions.append(year_tuition)
    total = len(tuitions)
    page = Page(total, _get_page_index())
    page = to_dict(page)
    start=page['offset']
    end=page['offset']+page['limit']
    if end > total:
        end=total
    tuitions=tuitions[start:end]
    return jsonify(tuitions=tuitions,k_classes=k_classes,page=page)	
	
@app.route('/api/year_tuition/delete',methods=['POST'])    #删除入园押金操作
@authorization('q3_1')
def  year_tuition_delete_api():
    r= request.json
    tuition_id = r['tuition_id']
    tuition =Year_Tuition.find_first('where id=?',tuition_id)
    if tuition:
        tuition.delete()
    return jsonify(tuition=tuition)	
	
	
@app.route('/deposit')     #入园押金缴费页面#
@authorization('q3_1')
def deposit():
    return render_template('deposit.html',page_index=_get_page_index())	
	
@app.route('/api/deposit')     #入园押金缴费信息# 
def deposit_load():
    k_classes =Class.find_by('where type=?','常规班')
    class_select = request.args.get('class_select')
    name=request.args.get('name')
    ispaid=request.args.get('ispaid')
    select_order='where tuition>0 '
    if name:
    	select_order=select_order +' and name like '+'\'%'+name+'%\''
    if class_select:
        select_order=select_order+' and k_class = '+'\''+class_select+'\''
    total = Kid.count_by(select_order)
    kids = Kid.find_by(select_order)
    j=0
    for i in range(len(kids)):
        tuition=Tuition.find_first('where kid_id=? and chargename=?',kids[j].id,'入园押金')
        if tuition:
            if ispaid=='未交':
                kids.pop(j)
                i=i+1
                j=j-1
                total=total-1
            else:
                kids[j].paid=tuition.paid
        else:
            if ispaid=='已交':
                kids.pop(j)
                i=i+1
                j=j-1
                total=total-1
            else:
                kids[j].paid=0
        j=j+1
    page = Page(total, _get_page_index())
    page = to_dict(page)
    start=page['offset']
    end=page['offset']+page['limit']
    if end > total:
        end=total
    kids=kids[start:end]
    return jsonify(kids=kids,page=page,k_classes=k_classes)	

	
	

@app.route('/api/deposit/add',methods=['POST'])    #入园押金缴费信息操作
@authorization('q3_1')
def  deposit_add_api():
    r= request.json
    kid_id = r['kid_id']
    now = int(time.time())   
    tuition=r['tuition']
    tuition = Tuition(kid_id=kid_id, time = now,paid= tuition,chargename='入园押金',month='')
    tuition.insert()
    return jsonify(tuition=tuition)

	
@app.route('/api/deposit/delete',methods=['POST'])    #删除入园押金操作
@authorization('q3_1')
def  deposit_delete_api():
    r= request.json
    kid_id = r['kid_id']
    tuition =Tuition.find_first('where kid_id=? and chargename=?',kid_id,'入园押金')
    if tuition:
        tuition.delete()
    return jsonify(tuition=tuition)	

@app.route('/article')     #入园杂费缴费页面#
@authorization('q3_1')
def article():
    return render_template('article.html',page_index=_get_page_index())	
	
@app.route('/api/article')     #入园杂费缴费信息# 
def article_load():
    k_classes =Class.find_by('where type=?','常规班')
    class_select = request.args.get('class_select')
    name=request.args.get('name')
    ispaid=request.args.get('ispaid')
    select_order='where tuition>0 '
    if name:
    	select_order=select_order +' and name like '+'\'%'+name+'%\''
    if class_select:
        select_order=select_order+' and k_class = '+'\''+class_select+'\''
    total = Kid.count_by(select_order)
    kids = Kid.find_by(select_order)
    j=0
    for i in range(len(kids)):
        article=Tuition.find_first('where kid_id=? and chargename=?',kids[j].id,'入园物品费')
        bedding=Tuition.find_first('where kid_id=? and chargename=?',kids[j].id,'床品费')
        test=Tuition.find_first('where kid_id=? and chargename=?',kids[j].id,'体验费')
        if article or bedding or test:
            if ispaid=='未交':
                kids.pop(j)
                i=i+1
                j=j-1
                total=total-1
            else:
                if article:
                    kids[j].article=article.paid
                else:
                    kids[j].article=0
                if bedding:
                    kids[j].bedding=bedding.paid
                else:
                    kids[j].bedding=0
                if test:
                    kids[j].test=test.paid 
                else:
                    kids[j].test=0
                kids[j].paid=kids[j].article+kids[j].bedding+kids[j].test
        else:
            if ispaid=='已交':
                kids.pop(j)
                i=i+1
                j=j-1
                total=total-1
            else:
                kids[j].paid=''
        j=j+1
    page = Page(total, _get_page_index())
    page = to_dict(page)
    start=page['offset']
    end=page['offset']+page['limit']
    if end > total:
        end=total
    kids=kids[start:end]
    article=Config.find_first('where 1=1').article
    bedding=Config.find_first('where 1=1').bedding
    test=Config.find_first('where 1=1').test
    return jsonify(kids=kids,page=page,k_classes=k_classes,article=article,test=test,bedding=bedding)	

	
@app.route('/api/article/add',methods=['POST'])    #入园杂费缴费信息操作
@authorization('q3_1')
def  article_add_api():
    r= request.json
    kid_id = r['kid_id']
    now = int(time.time())   
    tuition=r['article']
    tuition = Tuition(kid_id=kid_id, time = now,paid= tuition,chargename='入园物品费',month='')
    tuition.insert()
    tuition=r['bedding']
    tuition = Tuition(kid_id=kid_id, time = now,paid= tuition,chargename='床品费',month='')
    tuition.insert()
    tuition=r['test']
    tuition = Tuition(kid_id=kid_id, time = now,paid= tuition,chargename='体验费',month='')
    tuition.insert()
    return jsonify(tuition=tuition)
	
	
@app.route('/api/article/delete',methods=['POST'])    #删除入园物品费操作
@authorization('q3_1')
def  article_delete_api():
    r= request.json
    kid_id = r['kid_id']
    tuition=Tuition.find_first('where kid_id=? and chargename=?',kid_id,'入园物品费')
    if tuition:
        tuition.delete()    
    tuition=Tuition.find_first('where kid_id=? and chargename=?',kid_id,'床品费')
    if tuition:
        tuition.delete()    
    tuition=Tuition.find_first('where kid_id=? and chargename=?',kid_id,'体验费')
    if tuition:
        tuition.delete()
    return jsonify(tuition=tuition)	
	
	
	
#########################################################################################################
@app.route('/i_tuition')     #兴趣班缴费信息页面#
@authorization('q4_2')
def i_tuition():
    return render_template('interest_tuition.html',page_index=_get_page_index())	
	
@app.route('/api/i_tuition')     #兴趣班缴费信息# 
@authorization('')
def i_tuition_load():
    i_classes =Class.find_by('where type=? and close=0 order by create_date desc','兴趣班')
    class_select = request.args.get('class_select')
    ispaid=request.args.get('ispaid')	
    total = I_Class_kids.count_by( 'where class_id = ?',class_select)
    kids =I_Class_kids.find_by( 'where class_id = ?',class_select)
    j=0
    for i in range(len(kids)):
        i_tuition=I_Tuition.find_first ('where kid_id=?  and class_id=? and count=?',kids[j].kid_id,class_select,kids[j].class_count)
        if i_tuition:
            if ispaid=='未交或未退':
                kids.pop(j)
                i=i+1
                j=j-1
                total=total-1
            else:
                kids[j].paid=i_tuition.paid
        else:
            if ispaid=='已交或已退':
                kids.pop(j)
                i=i+1
                j=j-1
                total=total-1
            else:
                kids[j].paid=0
        j=j+1
    
    i_class=Class.get(class_select)
    for kid in kids:
        k_in_Kid=Kid.get(kid.kid_id)
        kid.id=k_in_Kid.id
        kid.name=k_in_Kid.name
        kid.tuition=i_class.tuition	
    page = Page(total, _get_page_index())
    page = to_dict(page)
    start=page['offset']
    end=page['offset']+page['limit']
    if end > total:
        end=total
    kids=kids[start:end]		
    return jsonify(kids=kids,i_classes=i_classes,page=page)	


	

@app.route('/api/i_tuition/add',methods=['POST'])    #兴趣班缴费的操作
def  i_tuition_add_api():
    r= request.json
    kid_id = r['kid_id']
    class_count = r['class_count']
    paid = r['paid']
    i_class=r['class_select']
    now = int(time.time())   
    tuition = I_Tuition(kid_id=kid_id, count = class_count,paid= paid,class_id=i_class,time=now)
    tuition.insert()
    return jsonify(tuition=tuition)	

@app.route('/api/i_tuition/check',methods=['POST'])    #查询某个学生是否有兴趣班缴费信息
def  i_tuition_check_api():
    r= request.json
    kid_id = r['kid']
    i_class=r['i_class']
    tuition = I_Tuition.find_first('where kid_id=? and class_id=?',kid_id,i_class)
    if tuition:is_tuition='y'
    else: is_tuition='n'
    return jsonify(is_tuition=is_tuition)		
	
@app.route('/api/i_tuition/delete',methods=['POST'])    #删除兴趣班缴费信息操作
@authorization('q4_2')
def  i_tuition_delete_api():
    r= request.json
    kid_id = r['kid_id']
    count=r['count']    
    i_class=r['class_select']
    tuition = I_Tuition.find_first('where kid_id=? and class_id=? and count=?',kid_id,i_class,count)
    if tuition:
        tuition.delete()  
    return jsonify(tuition=tuition)		
	
###################################出勤管理模块########################################		
@app.route('/rollcall')        #点名页面#
@authorization('q1_3')
def rollcall():
    return render_template('rollcall.html')


@app.route('/rollcall/modify')     #点名页面#
@authorization('')
def rollcall_modify():
    return render_template('rollcall_modify.html')
	
@app.route('/api/rollcall')     #点名信息# 
def kids_load():
    k_classes =Class.find_by('where type=?','常规班')
    k_class = request.args.get('class_select')
    date = request.args.get('date')
    if date:
	    day=date
    else:
        nowday=time.strftime("%Y-%m-%d")
        nowday=nowday+' 08:00:00'
        day=time.mktime(time.strptime(nowday,'%Y-%m-%d %H:%M:%S'))
    if k_class: 
        kids = Kid.find_by( 'where k_class=? order by name',k_class)
        for kid in kids:
            attendance=Attendance.find_by('where kid_id=? and day=? ',kid.id,day)
            if attendance:kid.be=False
            else: kid.be = True
    else:
        kids = []
    return jsonify(kids=kids,k_classes=k_classes)	
	
	
@app.route('/api/attendance/add',methods=['POST'])     #增加当天出勤信息# 
def attendance_add():
    r= request.json
    kids_notbe=r['kids_notbe']
    class_id=r['class_select']
    date = r['date']
    if date:
	    day=date
    else:
        nowday=time.strftime("%Y-%m-%d")
        nowday=nowday+' 08:00:00'
        day=time.mktime(time.strptime(nowday,'%Y-%m-%d %H:%M:%S'))
    kids_in = Attendance.find_by('where class_id=? and day=? ',class_id,day)
    if kids_in:
        for kid in kids_in:kid.delete()
    for kid_id in kids_notbe:
        attendance=Attendance(kid_id=kid_id, class_id=class_id,day=day)
        attendance.insert()    
    return	jsonify(kids_notbe={})
	
@app.route('/attendance')     #出勤表页面#
@authorization('')
def attendance():
    return render_template('attendance.html',page_index=_get_page_index())
	
@app.route('/api/attendance')     #出勤信息# 
def attendance_load():
    total = Kid.count_all()
    page = Page(total, _get_page_index())
    page = to_dict(page)
    k_classes =Class.find_by('where type=?','常规班')
    k_class = request.args.get('class_select')
    start_day = request.args.get('start_day')
    end_day = request.args.get('end_day')
    kids = Kid.find_by( 'where k_class=? order by name desc limit ?,?',k_class,page['offset'], page['limit'])
    for kid in kids:
        kids_attendance=Attendance.find_by('where kid_id=? and day>? and day<? ',kid.id,start_day,end_day)
        kid.attendance=[]
        for kid_at in kids_attendance:
            kid.attendance.append(kid_at.day)
    return jsonify(kids=kids,k_classes=k_classes,page=page)		
	
	
	
	
###################################幼儿管理模块########################################	
def _get_kids_by_page(size): 
    select_order = ''
    k_class = request.args.get('class_select')
    if k_class:
        if k_class =='未分配':
            select_order = 'where ((k_class =\'\') or (k_class is null))';
        else:
            select_order = 'where k_class='+'\''+k_class+'\'';   
    name = request.args.get('name')
    if name:
        if select_order :
            select_order = select_order +'and name like'+'\'%'+name+'%\'';
        else:
            select_order = 'where name like'+'\'%'+name+'%\'';
    total = Kid.count_by(select_order )
    page = Page(total, _get_page_index(),size)
    page = to_dict(page)		
			
    kids = Kid.find_by( select_order +' order by enter_date desc limit ?,?', page['offset'], page['limit'])
    for kid in kids:
        kid.k_class_name=''
        if kid.k_class:
            k_class=Class.get(kid.k_class)		
            kid.k_class_name=k_class.name
        kid.s_class_name=''        
        i_classes=I_Class_kids.find_by('where kid_id=?',kid.id)		
        for i_class in i_classes:
            kid.s_class_name=kid.s_class_name+' '+Class.get(i_class.class_id).name
    return kids, page

@app.route('/kid')     #幼儿信息页面#
@authorization('')
def kid():    
    return render_template('kid.html', page_index=_get_page_index())
	
@app.route('/api/kid')     #单个幼儿信息# 
def kid_load():
    kids, page = _get_kids_by_page(1)
    kid=kids[0]
    k_classes =Class.find_by('where type=?','常规班')
    return jsonify(kid=kid,page=page,k_classes=k_classes)
	
	
@app.route('/kids')     #幼儿信息列表#
def kids_view():
    return render_template('kids_view.html', page_index=_get_page_index())
	
@app.route('/api/kids')     #全部幼儿信息# 
def kid_all_load():
    kids, page = _get_kids_by_page(5)
    k_classes =Class.find_by('where type=?','常规班')
    return jsonify(kids=kids,page=page,k_classes=k_classes)
	
@app.route('/api/kid/<kid_id>')     #单个幼儿信息
def kid_one_load(kid_id):
    kid=Kid.get(kid_id)
    return jsonify(kid) 
	
@app.route('/kids/add')  #增加幼儿页面
@authorization('q1_1')
def kid_add():
    k_classes =Class.find_by('where type=?','常规班')
    tuition=Config.find_first('where 1=1').tuition
    return render_template('kid_edit.html',action= '/api/kid/add',tuition=tuition)

@app.route('/api/kid/add',methods=['POST'])    #增加幼儿操作
def  kid_add_api():
    r= request.json
    name = r['name']
    sex = r['sex']
    id_number = r['id_number']
    address= r['address']
    contacts1= r['contacts1']
    con1_name= r['con1_name']
    con1_phone= r['con1_phone']
    contacts2= r['contacts2']
    con2_name= r['con2_name']
    con2_phone= r['con2_phone']
    tuition=r['tuition']
    deposit=r['deposit']
    date= r['date']
    image= r['image']
    k_class=r['k_class']
    kid = Kid.find_first('where id_number=?', id_number)
    if kid:
        raise APIError('add:failed', 'id_number', 'id-number is already in use.')  
    if image: 
        local_url=re.compile('static/(.*)')
        image=local_url.search(image)
        image=image.group()
        copy(image, 'static/photo/kids')
        os.remove(image)
        image=image.replace('/uploads/','/kids/')
    kid = Kid(name=name, sex = sex,id_number= id_number,address= address,contacts1 = contacts1,con1_name = con1_name,con1_phone= con1_phone,contacts2 = contacts2,con2_name = con2_name,con2_phone= con2_phone,tuition=tuition,deposit=deposit,enter_date = date,image= image,k_class=k_class)
    kid.insert()	
    return jsonify(kid=kid)
	
@app.route('/kids/edit/<kid_id>')  #修改幼儿页面
@authorization('q1_2')
def kid_edit(kid_id):
    id = kid_id
    k_classes =Class.find_by('where type=?','常规班')
    return render_template('kid_edit.html',id = id,action='/api/kid/edit/%s' % id,k_classes=k_classes)	

@app.route('/api/kid/edit/<kid_id>',methods=['POST'])    #修改幼儿操作
def  kid_edit_api(kid_id):
    r= request.json
    kid = Kid.get(kid_id)
    kid.name = r['name']
    kid.sex = r['sex']
    kid.id_number = r['id_number']
    kid.address= r['address']
    kid.contacts1= r['contacts1']
    kid.con1_name= r['con1_name']
    kid.con1_phone= r['con1_phone']
    kid.contacts2= r['contacts2']
    kid.con2_name= r['con2_name']
    kid.con2_phone= r['con2_phone']
    kid.tuition=r['tuition']
    kid.deposit=r['deposit']
    kid.date= r['date']
    kid.k_class=r['k_class']
    image=r['image']
    local_url=re.compile('static/(.*)')
    image=local_url.search(image)
    image=image.group()	
    if not kid.image == image: 
        copy(image, 'static/photo/kids')		
        os.remove(image)
        os.remove(kid.image)
        kid.image=image.replace('/uploads/','/kids/')
    kid.update()
    return jsonify(kid=kid)
	
@app.route('/api/kid/<kid_id>/delete',methods=['POST'])
def api_delete_kid(kid_id):
    kid =Kid.get(kid_id)
    image=kid.image
    kid.delete()
    local_url=re.compile('static/(.*)')
    image=local_url.search(image)
    image=image.group()
    os.remove(image)
    return jsonify(kid_id=kid_id)	



def _get_i_kids_by_page(): 
    select_order = ''
    i_class = request.args.get('class_select')
    select_order = 'where class_id='+'\''+i_class+'\'';   
    kids = I_Class_kids.find_by( select_order +' order by enter_date')
    kids_id=[]
    for kid in kids:	    
        kid_count=I_Class_kids.count_by( select_order +' and kid_id =?',kid.kid_id)
        if (kid_count%2!=0):
            kids_id.append(kid.kid_id)
    kids_id = list(set(kids_id))
    total = len(kids_id)
    page = Page(total, _get_page_index())
    page = to_dict(page)
    start=page['offset']
    end=page['offset']+page['limit']
    if end > total:
        end=total
    kids_id=kids_id[start:end]
    kids=[]
    for kid_id in kids_id:
        kid={}
        kid['name']=Kid.get(kid_id).name
        kid['sex']=Kid.get(kid_id).sex
        kid['id_number']=Kid.get(kid_id).id_number
        kid['contacts1']=Kid.get(kid_id).contacts1
        kid['con1_name']=Kid.get(kid_id).con1_name
        kid['con1_phone']= Kid.get(kid_id).con1_phone		
        kid['k_class_name']=''
        k_class_id=Kid.get(kid_id).k_class
        if k_class_id:
            k_class=Class.get(k_class_id)		
            kid['k_class_name']=k_class.name
        kids.append(kid)			
    return kids, page

@app.route('/i_class_kids')     #幼儿加入特长班页面#
@authorization('q4_1')
def i_class_kids():
    return render_template('i_class_kids.html')

@app.route('/i_class')     #特长班信息页面#
@authorization('')
def i_class():
    return render_template('i_class.html', page_index=_get_page_index())
	
@app.route('/api/i_class')     #特长班信息#
def i_class_load():	
    kids, page = _get_i_kids_by_page()
    k_classes =Class.find_by('where type=? and close=0 order by create_date desc','兴趣班')
    return jsonify(kids=kids,page=page,k_classes=k_classes)
	
	
@app.route('/api/i_class_kids')     #幼儿 特长班信息# 
def i_class_kids_load():
    i_class_id = request.args.get('i_class_select')
    kids = Kid.find_all()
    for kid in kids:
        i_class_kids=I_Class_kids.find_by('where kid_id=? and class_id=?',kid.id,i_class_id)		
        if len(i_class_kids)%2!=0:
            kid.is_i_class=1
        else:
            kid.is_i_class=0
    k_classes =Class.find_by('where type=?','常规班')
    i_classes =Class.find_by('where type=? and close=0 order by create_date desc','兴趣班')
    i_class=Class.get(i_class_id)    
    return jsonify(kids=kids,k_classes=k_classes,i_classes=i_classes,i_class=i_class)	

	
@app.route('/api/i_class_kids/add')     #幼儿 特长班信息-----插班操作# 
def i_class_kid_add_add():
    i_kid = request.args.get('i_kid') 
    i_class_select = request.args.get('i_class_select')
    date = int(time.time())
    class_count=request.args.get('class_count')
    i_kid_class =I_Class_kids(kid_id=i_kid,class_id=i_class_select,enter_date=date,class_count=class_count)
    i_kid_class.insert()
    return jsonify(kid=i_kid)	
	
@app.route('/api/i_class_kid/leave',methods=['POST'])
def api_delete_i_class_kids():
    r= request.json
    kid=r['kid']
    i_class=r['i_class']
    class_count=r['class_count']
    date = int(time.time())
    i_tuition=I_Tuition.find_by('where kid_id=? and class_id=?',kid,i_class)
    if i_tuition:
        i_kid_class =I_Class_kids(kid_id=kid,class_id=i_class,enter_date=date,class_count=class_count)
        i_kid_class.insert()
    else:
        i_class_kid=I_Class_kids.find_first('where kid_id=? and class_id=?',kid,i_class)
        i_class_kid.delete()    
    return jsonify(kid=kid)	
	
###################################教师管理模块########################################	
def _get_teachers_by_page():
    select_order = ''
    type=request.args.get('type')
    class_select = request.args.get('class_select')
    name = request.args.get('name')
    if type:
        select_order = 'where t_type='+'\''+type+'\''		
    if class_select:
        if class_select =='未分配':
            k_classes=Class.find_all()
            class_teachers=''
            for k_class in k_classes:
                teachers=k_class.teachers.split(',')
                for teacher in teachers:
                    class_teachers=class_teachers + '\''+str(teacher)+'\','
            thisorder=' name not in ('+class_teachers+'\'\')'
        else:
            k_class=Class.get(class_select);
            teachers=k_class.teachers.split(',')
            class_teachers=''
            for teacher in teachers:
                if teacher:
                    class_teachers=class_teachers + '\''+str(teacher)+'\','
            thisorder=' name in ('+class_teachers+'\'\')'
        if select_order:
            select_order = select_order +' and '+ thisorder
        else:        
            select_order = ' where ' + thisorder
    if name:
        if select_order :
            select_order = select_order +'and name like'+'\'%'+name+'%\''
        else:
            select_order = 'where name like'+'\'%'+name+'%\''
    total = Teacher.count_by(select_order)   
    page = Page(total, _get_page_index())
    page = to_dict(page)
    teachers = Teacher.find_by( select_order +' order by enter_date desc limit ?,?', page['offset'], page['limit'])
    for teacher in teachers:
        teacher.class_name=''
        for k_class in Class.find_all():
            if teacher.name in k_class.teachers:
                teacher.class_name=teacher.class_name+k_class.name+','        
    return teachers, page,

@app.route('/teachers')     #教师信息页面#
@authorization('')
def teacher_view():
    return render_template('teachers_view.html', page_index=_get_page_index())
	
@app.route('/api/teachers')     #全部教师信息#
def teacher_all_load():
    type=request.args.get('type')
    teachers, page = _get_teachers_by_page()
    classes =Class.find_by('where type=?',type)
    return jsonify(teachers=teachers,page=page,classes=classes)
	
@app.route('/api/teachers/all',methods=['POST'])     #不同类别教师信息#
def teacher_selected_load():
    teachers=Teacher.find_all('')
    return jsonify(teachers=teachers) 
	

@app.route('/api/teacher/<teacher_id>')     #单个教师信息
def teacher_one_load(teacher_id):
    teacher=Teacher.get(teacher_id)
    return jsonify(teacher) 
	
@app.route('/teachers/add')  #增加教师页面
@authorization('q2_1')
def teacher_add():
    return render_template('teacher_edit.html',action= '/api/teacher/add')

@app.route('/api/teacher/add',methods=['POST'])    #增加教师操作
def  teacher_add_api():
    r= request.json
    name = r['name']
    sex = r['sex']
    id_number = r['id_number']
    educational= r['educational']
    university= r['university']
    specialty= r['specialty']
    phone= r['phone']
    date= r['date']
    image= r['image']
    t_type=r['t_type']
    teacher = Teacher.find_first('where id_number=?', id_number)
    if teacher:
        raise APIError('add:failed', 'id_number', 'id-number is already in use.')  
    if image: 
        local_url=re.compile('static/(.*)')
        image=local_url.search(image)
        image=image.group()
        copy(image, 'static/photo/teachers')
        rmtree('static/photo/uploads')
        os.mkdir('static/photo/uploads')
        image=image.replace('/uploads/','/teachers/')
    teacher = Teacher(name=name, sex = sex,id_number= id_number,educational= educational,university = university,specialty = specialty,phone= phone,enter_date = date,image= image,t_type=t_type)
    teacher.insert()
    return jsonify(teacher=teacher)
	
@app.route('/teachers/edit/<teacher_id>')  #修改教师页面
@authorization('q2_2')
def teacher_edit(teacher_id):
    id = teacher_id
    return render_template('teacher_edit.html',id = id,action='/api/teacher/edit/%s' % id)	

@app.route('/api/teacher/edit/<teacher_id>',methods=['POST'])    #修改教师操作
def  teacher_edit_api(teacher_id):
    r= request.json
    teacher = Teacher.get(teacher_id)
    teacher.name = r['name']
    teacher.sex = r['sex']
    teacher.id_number = r['id_number']
    teacher.educational= r['educational']
    teacher.university= r['university']
    teacher.specialty= r['specialty']
    teacher.phone= r['phone']
    teacher.date= r['date']
    image=r['image']
    teacher.t_type=r['t_type']
    local_url=re.compile('static/(.*)')
    image=local_url.search(image)
    image=image.group()	
    if not teacher.image == image: 
        copy(image, 'static/photo/teachers')		
        rmtree('static/photo/uploads')
        os.mkdir('static/photo/uploads')
        os.remove(teacher.image)
        teacher.image=image.replace('/uploads/','/teachers/')
    teacher.update()
    return jsonify(teacher=teacher)
	
@app.route('/api/teacher/<teacher_id>/delete',methods=['POST'])
def api_delete_teacher(teacher_id):
    teacher =Teacher.get(teacher_id)
    image=teacher.image
    teacher.delete()
    local_url=re.compile('static/(.*)')
    image=local_url.search(image)
    image=image.group()
    os.remove(image)
    return jsonify(teacher_id=teacher_id)
	

##################################班级管理模块########################################	

@app.route('/classes')     #班级信息页面#
@authorization('')
def class_view():
    return render_template('classes_view.html', page_index=_get_page_index())
	
def _get_classes_by_page():    #班级分页#
    type=request.args.get('type')
    select_order=''
    if type:
        select_order='where type='+'\''+type+'\''	
    total = Class.count_by(select_order)
    page = Page(total, _get_page_index())
    page = to_dict(page)
    classes =Class.find_by(select_order+' order by create_date desc limit ?,?', page['offset'], page['limit'])
    return classes, page
	
@app.route('/api/classes')     #全部班级信息#
def class_all_load():
    classes, page = _get_classes_by_page()
    return jsonify(classes=classes,page=page) 	
	
@app.route('/api/classes/<type>',methods=['POST'])     #不同类别#
def classes_selected_load(type):
    classes=Class.find_by('where type=?', type)
    return jsonify(classes=classes) 	

@app.route('/api/class/<class_id>')     #单个班级信息
def class_one_load(class_id):
    class_w=Class.get(class_id)
    if not class_w.teachers:
        class_w.teachers=''
    class_w.teachers=class_w.teachers.split(',')   
    return jsonify(class_w) 
	
@app.route('/classes/add')  #增加班级页面
@authorization('q2_3')
def class_add():
    return render_template('class_edit.html',action= '/api/class/add')

@app.route('/api/class/add',methods=['POST'])    #增加班级操作
@authorization('q2_3')
def  class_add_api():
    r= request.json
    name = r['name']
    type = r['type']
    tuition = r['tuition']
    class_count = r['class_count']
    other_charge_name = r['other_charge_name']
    other_charge = r['other_charge']
    close=r['close']    
    primary_teacher = r['primary_teacher']
    teachers= r['teachers']
    tea=''
    for t in teachers:
	    tea=tea+t+','
    create_date= r['date']
    class_w = Class(name=name, type = type,tuition= tuition,create_date = create_date,teachers=tea,primary_teacher=primary_teacher,class_count=class_count,other_charge=other_charge,other_charge_name=other_charge_name,close=close)
    class_w.insert()
    return jsonify(class_w=class_w)
	
@app.route('/class/edit/<class_id>')  #修改班级页面
@authorization('q2_4')
def class_edit(class_id):
    id = class_id
    return render_template('class_edit.html',id = id,action='/api/class/edit/%s' % id)	

@app.route('/api/class/edit/<class_id>',methods=['POST'])    #修改班级操作
def  class_edit_api(class_id):
    r= request.json
    class_w = Class.get(class_id)
    class_w.name = r['name']
    class_w.type = r['type']
    class_w.tuition = r['tuition']
    class_w.class_count= r['class_count']
    class_w.other_charge_name=r['other_charge_name']
    class_w.other_charge=r['other_charge'] 
    class_w.close=r['close']	
    class_w.primary_teacher = r['primary_teacher']	
    teachers= r['teachers']
    tea=''
    for t in teachers:
	    tea=tea+t+','
    class_w.teachers= tea
    class_w.create_date= r['date']
    class_w.update()
    return jsonify(class_w=class_w)
	
@app.route('/api/class/<class_id>/delete',methods=['POST'])
def api_delete_class(class_id):
    class_w =Class.get(class_id)
    class_w.delete()
    return jsonify(class_id=class_id)