# -*- coding: utf-8 -*-
# @Time    : 2018/4/22 15:58
# @Author  : YuChou
# @Site    : 
# @File    : Clish.py
# @Software: PyCharm
import pexpect
import re
import logging
import time
import json

class HongZhouclish():
    def __new__(cls, *args, **kwargs):
        pass
    #定义类输入 初始化需要输入的参数
    def __init__(self, host='192.168.1.200',port = 22, user = "root", password = "root", logfile = "test_ota.log"):
        self.host=host
        self.port=port
        self.user=user
        self.password=password
        logging.basicConfig(filename = logfile, level = logging.DEBUG, format='%(asctime)s %(message)s')
        self.session = self.__openClish(self.host,self.port, self.user, self.password)#获取进程会话窗口

    #创建会话 此函数不提供外部调用
    def __openClish(self,host,port,user,password):
        cmd = 'ssh -p %d %s@%s' % (port, user, host)
        logging.info(cmd)
        session = pexpect.spawn(cmd)
        session.expect('password')
        session.sendline(password)
        session.expect('#')
        session.sendline('clish')
        session.expect('>')
        return session

    #得到list-self下的会话信息
    def get_GWSL_GWFL_id(self):
        cmd='list-self'
        self.session.send(cmd)
        self.session.expect('>')#直到出现'>'
        if self.session.before:
            list_self_list=self.session.before.split('\n\r')
            return list_self_list
        else:
            logging.debug('连接出现问题')
            return None

    def parser_List_self(self):
        content=self.get_GWSL_GWFL_id()
        pass




    #调用该函数可以得到list-bar命令下的显示
    def get_Listbar(self,GWSL_ID):
        cmd='list-bar '+GWSL_ID
        self.session.send(cmd)
        self.session.expect('>')
        pass

if __name__=="__main__":
    pass