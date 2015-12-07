#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
Models for user, blog, comment.
'''

import time, uuid

from transwarp.db import next_id
from transwarp.orm import Model, StringField, BooleanField, FloatField, TextField,IntegerField,DoubleField

class Dict(dict):
    '''
    Simple dict but support access as x.y style.
    >>> d1 = Dict()
    >>> d1['x'] = 100
    >>> d1.x
    100
    >>> d1.y = 200
    >>> d1['y']
    200
    >>> d2 = Dict(a=1, b=2, c='3')
    >>> d2.c
    '3'
    >>> d2['empty']
    Traceback (most recent call last):
        ...
    KeyError: 'empty'
    >>> d2.empty
    Traceback (most recent call last):
        ...
    AttributeError: 'Dict' object has no attribute 'empty'
    >>> d3 = Dict(('a', 'b', 'c'), (1, 2, 3))
    >>> d3.a
    1
    >>> d3.b
    2
    >>> d3.c
    3
    '''
    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value


class Config(Model):
    __table__='config'
    
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')	
    kindergarten=StringField(ddl='varchar(50)')
    month_start=IntegerField(default=1)
    discount=FloatField()
    foodcosts=FloatField()
    tuition=FloatField()
    article=FloatField()
    bedding=FloatField()
    test=FloatField()
	
	
class Special_charge(Model):
    __table__='special_charge'
    
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')	
    chargename=StringField(ddl='varchar(50)')
    month= StringField(ddl='varchar(50)')
    class_id=StringField(ddl='varchar(50)')
    charge=FloatField()
	


class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    name = StringField(ddl='varchar(50)')
    password = StringField(ddl='varchar(50)')
    admin = StringField(ddl='varchar(150)')

class Kid(Model):
    __table__ = 'kids'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    name = StringField(ddl='varchar(50)')
    sex=StringField(ddl='varchar(4)')
    id_number=StringField(updatable=False,ddl='varchar(18)')
    address=StringField(ddl='varchar(50)')
    contacts1=StringField(ddl='varchar(10)')
    con1_name=StringField(ddl='varchar(10)')
    con1_phone=StringField(ddl='varchar(20)')
    contacts2=StringField(ddl='varchar(10)')
    con2_name=StringField(ddl='varchar(10)')
    con2_phone=StringField(ddl='varchar(20)')
    tuition=FloatField()
    deposit=FloatField()
    enter_date=FloatField(default=time.time)
    exist=BooleanField()
    image=StringField(ddl='varchar(500)')
    k_class=StringField(ddl='varchar(50)')

	
class Teacher(Model):
    __table__ = 'teachers'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    name = StringField(ddl='varchar(50)')
    sex=StringField(ddl='varchar(4)')
    id_number=StringField(updatable=False,ddl='varchar(18)')
    educational=StringField(ddl='varchar(50)')
    university=StringField(ddl='varchar(50)')
    specialty=StringField(ddl='varchar(50)')
    phone=StringField(ddl='varchar(20)')
    enter_date=FloatField(default=time.time)
    image=StringField(ddl='varchar(500)')
    t_type=StringField(ddl='varchar(50)')



class Class(Model):
    __table__ = 'class'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    name = StringField(ddl='varchar(50)')
    create_date = FloatField(default=time.time)    
    type = StringField(ddl='varchar(50)')
    primary_teacher = StringField(ddl='varchar(50)')
    teachers = StringField(ddl='varchar(200)')
    tuition = FloatField()
    class_count=IntegerField()
    other_charge_name=StringField(ddl='varchar(50)')
    other_charge= FloatField()
    close=BooleanField()


class I_Class_kids(Model):
    __table__ = 'i_class_kids'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    kid_id = StringField(ddl='varchar(50)')
    class_id = StringField(ddl='varchar(50)')
    class_count = IntegerField()
    enter_date = StringField(ddl='varchar(50)')

class Attendance(Model):
    __table__ = 'attendance'
	
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    kid_id = StringField(ddl='varchar(50)')
    class_id = StringField(ddl='varchar(50)')
    day = DoubleField(default=time.time)
	
class Tuition(Model):
    __table__ = 'tuition'
	
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    kid_id = StringField(ddl='varchar(50)')
    time = StringField(ddl='varchar(50)')
    paid = FloatField()
    chargename = StringField(ddl='varchar(20)')
    month = StringField(ddl='varchar(50)')

class Year_Tuition(Model):
    __table__ = 'year_tuition'
	
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    kid_id = StringField(ddl='varchar(50)')
    time = StringField(ddl='varchar(50)')
    paid = FloatField()
    start_month = StringField(ddl='varchar(50)')
    end_month = StringField(ddl='varchar(50)')

class I_Tuition(Model):
    __table__ = 'i_tuition'
	
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    kid_id = StringField(ddl='varchar(50)')
    class_id = StringField(ddl='varchar(50)')
    count = IntegerField()
    paid = FloatField()	
    time = StringField(ddl='varchar(50)')