# -*- encoding: utf-8 -*-
import pexpect
import sys
import re
import logging
from datetime import datetime
import time
import json
class Clish():
    def __init__(self, gatewayIp, port = 22, user = "root", password = "root", logfile = "test_ota.log"):
        self.gatewayIp = gatewayIp
        self.logfile = logfile
        logging.basicConfig(filename = logfile, level = logging.DEBUG, format='%(asctime)s %(message)s')
        self.session = self.openCli(gatewayIp, port, user, password)#获取进程会话窗口


        #分析源码 session会话窗口 .sendline()方法发送指令到命令行

     #获取所有二级网关 和一级网关
    def listShelfs(self, shelf_gateways):
        session = self.session
        session.sendline('list-shelf')
        session.expect('> ')
        lines = session.before.split("\r\n")

        for index,line in enumerate(lines):
            if index < 5:
                continue
            cols = line.split()
            if not cols:
                break

            id = int(cols[0])

            shelf_gateways.append(id)


        return self

        #获取所有在线网关
    def listOnlineShelfs(self, shelf_gateways):
        session = self.session
        session.sendline('list-shelf')
        session.expect('> ')
        #获取所有行
        lines = session.before.split("\r\n")#换行 回车符号

        for index,line in enumerate(lines):
            #判断5列之内Device ID  Type    Version        State     SN五个属性
            if index < 5:
                continue
            cols = line.split()
            if not cols:
                break

            if cols[3] != "Online":#第四列是在线网关 第0列是网关ID
                continue

            id = int(cols[0])
            shelf_gateways.append(id)#网关列表

        return self#返回网关列表

        #返回SN码
    def listOnlineShelfsSN(self, shelf_gateways):
        session = self.session
        session.sendline('list-shelf')
        session.expect('> ')
        lines = session.before.split("\r\n")

        shelf = {}
        for index,line in enumerate(lines):
            if index < 5:
                continue
            cols = line.split()
            if not cols:
                break

            if cols[3] != "Online":
                continue

            id = int(cols[0])

            chipid_sn = cols[4].split(":")
            if len(chipid_sn) != 2:
                print( "invalid cols[4]:%s %s" % (cols[4], line))
                continue

            (chip_id, device_sn) = cols[4].split(":")
            shelf_gateways.append({"sn": device_sn,
                                   "id": id})

        return self

       #获取二级网关下的所有bar ID
    def listBar(self, shelf, bars):
        session = self.session
        session.sendline('list-bar %d ' % (shelf))
        session.expect('> ')
        lines = session.before.split("\r\n")

        for index,line in enumerate(lines):
            if index < 5:
                continue

            cols = line.split()
            if not cols:
                break

            try:
                id = int(cols[0])
            except:
                print( "invalid id, line:%s" % (line))
                continue

            bars.append(id)
        return self


        #查询每个device的信息
    def info(self, shelf, device_info):
        session = self.session
        session.sendline('info %d' % (shelf))
        session.expect('> ')
        match_all = re.S#包括\n符号的正则匹配
        device_info.append(session.before)
        return self
        #得到版本
    def getVersion(self, device_info):
        lines = device_info.split("\r\n")
        if len(lines) < 5:
            return ""
        else:
            v = lines[4].split()
            if len(v) < 3:
                print( "invalid sn, line:%s" % (lines[4]))
                return ''
            return lines[4].split()[2]

#得到SN
    def getSN(self, device_info):
        lines = device_info.split("\r\n")
        if len(lines) < 5:
            return ""
        else:
            sn = lines[3].split()
            if len(sn) < 3:
                print( "invalid sn, line:%s" % (lines[3]))
                return ''
            return lines[3].split()[2]
#得到Id
    def getID(self, device_info):
        lines = device_info.split("\r\n")
        if len(lines) < 5:
            return ""
        else:
            id = lines[1].split()
            if len(id) < 3:
                print( "invalid id, line:%s" % (lines[1]))
                return ''
            return lines[1].split()[2]
#得到类型
    def getType(self, device_info):
        lines = device_info.split("\r\n")
        if len(lines) < 5:
            return ""
        else:
            type = lines[2].split()
            if len(type) < 3:
                print( "invalid type, line:%s" % (lines[2]))
                return ''
            return lines[2].split()[2]
#得到设备所有属性
    def getDeviceAttr(self, shelf):
        device_info = []
        self.info(shelf, device_info)
        device_info = device_info[0]
        id = self.getID(device_info)
        sn = self.getSN(device_info)
        type = self.getType(device_info)
        version = self.getVersion(device_info)
        if len(id) == 0:
            print( "info:%s" % (device_info))
            return None

        return {
            "id": id,
            "sn": sn,
            "type": type,
            "version": version
        }

    def listDeviceAttr(self):
        attrs = []
        """
        shelfs = [
            202,
            208,
            210,
            174,
            175,
            214,
            215,
            216,
            217,
            218,
            242,
            258,
            367,
            308,
            316,
            249,
            250,
            251,
            252,
            253,
            254,
            256,
            190
        ]
        """
        shelfs = []
        self.listOnlineShelfsSN(shelfs)
        for shelf in shelfs:
            shelf_id = shelf["id"]
            shelf_id = shelf
            attr = self.getDeviceAttr(shelf_id)
            if attr:
                attrs.append(attr)
            else:
                print( "invalid attr, shelf id:%d" % (shelf_id))
                time.sleep(2)
                continue

            bars = []
            self.listBar(shelf_id, bars)
            for bar_id in bars:
                attr = self.getDeviceAttr(bar_id)
                if attr:
                    attrs.append(attr)
                else:
                    print( "invalid attr, bar id:%d" % (bar_id))
                    time.sleep(2)
        return attrs
        #利用pexcept(只能在linux下环境调用的库)打开clish的交互环境方法：
    def openCli(self, host, port, user, passwod):
        cmd = 'ssh -p %d %s@%s' % (port, user, host)
        logging.info(cmd)
        session = pexpect.spawn(cmd)
        session.expect('password')
        session.sendline(passwod)
        session.expect('#')
        session.sendline("cat /proc/net/can/reset_stats")
        session.expect('#')
        session.sendline('clish')
        session.expect('>')
        return session


    def otaShelf(self, shelf, url, result):
        session = self.session
        cmd = "ota %d %s " % (shelf, url)
        print( cmd)
        logging.info(cmd)

        start = time.time()
        try:
            session.sendline(cmd)
            session.expect('100%  OTA', timeout=120)
            session.expect('Device Online', timeout=10)
        except pexpect.TIMEOUT:
            msg = "ota %d failed" % (shelf)
            print( msg)
            logging.fatal(msg)
            #logging.fatal(session.before)
            result.append(False)
            return self

        end = time.time()
        used_time = end - start
        msg = "ota %d ok, use %ds" % (shelf, used_time)
        print( msg)
        logging.info(msg)
        result.append(True)
        return self

    def onlines(self, devices, online):
        session = self.session
        for device in devices:
            session.sendline('info %d' % (device))
            session.expect('> ')

            match_all = re.S
            if re.match(".*timeout", session.before, match_all):
                msg = "%d offline" % (device)
                print( msg)
                logging.debug(msg)
                time.sleep(2)
            else:
                online.append(device)
                msg = "%d online" % (device)
                print( msg)
                logging.debug(msg)

        return self

    def onlineInfo(self, shelfs, infos):
        device_info = []
        for shelf in shelfs:
            #print( "shelf:%d" % (shelf))
            session = self.session
            session.sendline('list-bar %d ' % (shelf))
            session.expect('> ')
            lines = session.before.split("\r\n")
            for index,line in enumerate(lines):
                if index < 4:
                    continue

                cols = line.split()
                if not cols:
                    #print( "invalid line:%s" % (line))
                    break

                #print( "valid line:%s" % (line))
                #if cols[3] != "Online":
                #    continue;
                device_info = []
                self.info(shelf, device_info)
                match_all = re.S
                if re.match(".*timeout", device_info[0], match_all):
                    print( "%d offline" % (shelf))
                    continue

                chipid_sn = cols[4].split(":")
                if len(chipid_sn) != 2:
                    print( "invalid cols[4]:%s %s" % (cols[4], line))
                    continue

                (chip_id, sn) = cols[4].split(":")
                infos.append({
                    "id": int(cols[0]),
                    "type": cols[1],
                    "chip_id": chip_id,
                    "sn": sn,
                    "layer": int(cols[6]),
                    "shelf": shelf
                })

        return self

    def _findShelfId(self, shelf_id, device_info):
        for device in device_info:
            if shelf_id == device["id"]:
                return device

        return None


    def _findShelf(self, shelf_sn, device_info):
        for device in device_info:
            #print( "shelf_sn:%s device_sn:%s" % (shelf_sn, device["sn"]))
            if re.match(shelf_sn, device["sn"]):
                return device

        return None

    def _findBars(self, shelf_id, devices, device_info):
        for device in device_info:
            if device["shelf"] == shelf_id:
                devices.append(device)

    def shelfDevicesId(self, shelf_id, device_info):
        devices = []
        shelf = self._findShelfId(shelf_id, device_info)
        if not shelf:
            print( "cannot find %s" % (shelf_sn))
            return devices

        self._findBars(shelf["id"], devices, device_info)
        return devices



    def shelfDevicesSn(self, shelf_sn, device_info):
        devices = []
        shelf = self._findShelf(shelf_sn, device_info)
        if not shelf:
            print( "cannot find %s" % (shelf_sn))
            return devices

        self._findBars(shelf["id"], devices, device_info)
        return devices

    def _findConfBar(self, layer, shelf):
        for bar in shelf["bars"]:
            if layer == bar["layerIndex"]:
                return bar
        return None

    def _findEtagPath(self, layer, shelf):
        etag = []
        bar = self._findConfBar(layer, shelf)
        if not bar:
            print( "layer:%d not found on shelf %s" % (layer, shelf["sn"]))
            return etag

        #print( json.dumps(bar, ensure_ascii = False, indent = 2))
        for i in range(0,9):
            etag.append('')

        for sku in bar["skus"]:
            for i in range(sku["startIndex"] - 1, sku["endIndex"]):
                etag[i] = sku['imageId']
        return etag

    def _findShelfWithBar(self, bar, shelfs):
        shelf_id = bar["shelf"]
        for (key,value) in shelfs.items():
            if int(key) == shelf_id:
                return shelfs[key]

        key = str(shelf_id)
        shelfs[key] = []
        return shelfs[key]

    def _sort2shelf(self, bar_etags):
        shelfs = {}
        for bar in bar_etags:
            shelf = self._findShelfWithBar(bar, shelfs)
            shelf.append(bar)
        return shelfs

    def _setupEtagsConf(self, device_info, conf):
        bar_etags = self._getEtags(device_info, conf)
        return self._sort2shelf(bar_etags)

    def setupOneShelf(self, cmds):
        session = self.session
        for cmd in cmds:
            print( "cmd:%s" % (cmd))
            #continue # TODO: should be removed
            try:
                session.sendline(cmd)
                session.expect('is writing', timeout=15)
                msg = "%s, is writing" % (cmd)
                print( msg)
                logging.info(msg)
                time.sleep(15)
            except pexpect.TIMEOUT:
                msg = "%s failed" % (cmd)
                print( msg)
                logging.fatal(msg)


        return self

    def setupEtag(self, conf, shelf):
        session = self.session
        if shelf:
            print( "setup one shelf:%s" % (shelf))
            if conf.has_key(shelf):
                self.setupOneShelf(conf[shelf])
            else:
                print( "shelf:%s not found" % (shelf))
            return self

        for (shelf, cmds) in conf.items():
            print( "setup shelf:%s" % (shelf))
            self.setupOneShelf(cmds)
            return self

    def setupEtagCmds(self, device_info, conf, url):
        etags = self._setupEtagsConf(device_info, conf)
        #print( json.dumps(etags, ensure_ascii = False, indent = 2))
        etag_conf = {}
        for (key,value) in etags.items():
            cmds = []
            for etag_index in range(0, 9):
                for index,bar in enumerate(value):
                    etag = bar["etags"]
                    if len(etag) != 9:
                        print( "etag not found on bar %s, id:%d" % (bar["sn"], bar["id"]))
                        continue

                    cmd = "set-etag %d %d %s/%s" % (bar["id"], etag_index + 1, url, etag[etag_index])
                    print( "key:%s cmd:%s" % (key, cmd))
                    cmds.append(cmd)
            etag_conf[key] = cmds

        #print( json.dumps(etag_conf, ensure_ascii = False, indent = 2))
        return etag_conf

    def _getEtags(self, device_info, conf):
        jsonFile = open('beijing_etag.json', 'r')
        jsonObj = json.load(jsonFile)
        bar_etags = []
        for index,shelf in enumerate(jsonObj["shelfs"]):
            sn = shelf["sn"]
            if not sn or len(sn) == 0:
                continue

            #print( "shelf sn:%s" % (sn))
            devices = cli.shelfDevicesSn(sn, device_info)
            etag_devices = []
            if devices:
                for device in devices:
                    if device["type"] != "SS02" and device["type"] != "SS03":
                        continue
                    etag_devices.append(device)

            for i in range(0, len(etag_devices) - 1):
                if etag_devices[i]["type"] == "SS02" and etag_devices[i + 1]["type"] == "SS03":
                    print( "device:%d is not have etag" % (etag_devices[i]["id"]))
                    etag_devices.pop(i)
                    break

            etag_devices.sort(key = lambda k : (k.get('id'), 0))
            """
            for idx,v in enumerate(etag_devices):
                print( "idx:%d id:%d" % (idx, v["id"]))
            """

            etag_index = 1
            for device in etag_devices:
                etags = self._findEtagPath(etag_index, shelf)
                #print( "bar:%s id:%d type:%s" % (device["sn"], device["id"], device["type"]))
                #print( etags)
                device["etags"] = etags
                bar_etags.append(device)
                etag_index += 1
                #print( json.dumps(devices, ensure_ascii = False, indent = 2))

        jsonFile.close()
        return bar_etags

    def findDeviceWithSN(self, device_sn, online_shelfs):
        device_sn = device_sn.lower()
        for shelf in online_shelfs:
            if re.match(device_sn, shelf["sn"]):
                #print( "sn:%s == device_sn:%s, id:%d" % (shelf["sn"], device_sn, shelf["id"]))
                return shelf["id"]
        return -1

    def turnOffNotify(self):
        self.sendCmd("notify off")
        return self

    def turnOnNotify(self):
        self.sendCmd("notify on")
        return self


    def sendCmd(self, cmd, exp = "> ", timeout_sec = 10):
        session = self.session
        session.sendline(cmd)
        session.expect(exp, timeout = timeout_sec)
        #print( session.before)
        return self

    def setAxis(self, conf_path, online_shelfs):
        jsonFile = open('sn_beijing_etag.json', 'r')
        jsonObj = json.load(jsonFile)
        for shelf in jsonObj["shelfs"]:
            (sn, x1, y1, x2, y2) = (shelf["sn"], shelf["x1"], shelf["y1"], shelf["x2"], shelf["y2"])
            #print( "sn:%s x1:%d y1:%d x2:%d y2:%d" % (sn, x1, y1, x2, y2))
            id = self.findDeviceWithSN(shelf["sn"], online_shelfs)
            if id <= 0:
                print( "cannot find id from sn:%s" % (shelf["sn"]))
                continue

            cmd = "set-axis %d %d %d %d %d" % (id, x1, y1, x2, y2)
            print( "sn:%s cmd:%s" % (sn, cmd))
            self.sendCmd(cmd, "OK")
        jsonFile.close()
        return self

def updateSNs(self, conf_path, sn_file):
    jsonFile = open(conf_path, 'r')
    newJsonFile = open("sn_" + conf_path, 'w')
    jsonObj = json.load(jsonFile)

    snFile = open(sn_file, 'r')
    for (index,line) in enumerate(snFile.readlines()):
        if index == 0:
            continue

        cols = line.split(",")
        if len(cols) < 4:
            continue
        (group, shelfIndex, id, sn) = (cols[0], cols[1], cols[2], cols[3])
        print( "sn:%s" % (sn))
        jsonObj["shelfs"][index - 1]["sn"] = sn


    newJsonFile.write(json.dumps(jsonObj, ensure_ascii = False, indent = 2).encode('UTF-8'))
    newJsonFile.close()
    jsonFile.close()
    snFile.close()
    return self


def checkVersion(attrs, versions):
    old_attr = []
    for attr in attrs:
        device_type = attr["type"]
        device_version = attr["version"]
        if not versions.has_key(device_type):
            print( "unkown type:%s" % (device_type))
            continue

        last_version = versions[device_type]
        if device_version != last_version:
            print( "last_version:%s" % (last_version))
            print( attr)
            old_attr.append(attr)

    return old_attr

if __name__ == "__main__":
    cli = Clish("127.0.0.1", port = 9000, user = "root", password = "Smartadmin123!")
    cli.turnOffNotify()
    attrs = cli.listDeviceAttr()
    attrs = checkVersion(attrs, {
        "GW02": "1.0.19",
        "SS01": "1.0.51",
        "SS02": "1.0.36",
        "SS03": "1.0.12"
    })
    print( attrs)
    jsonFile = open('old_versions.json', 'w')
    json.dump(attrs, jsonFile, ensure_ascii = False, indent = 2)
    jsonFile.close()

    """
    cli.listOnlineShelfs(shelfs)\
        .onlineInfo(shelfs, device_info)\
        #.onlines(bars, bar_onlines)\
        #otaShelf(onlines[0], " http://192.168.2.103:6000/SR-GW02-SD01-A000-FN0-H000-V1.0.19.ota", ota_result)

    """

    """
    conf = cli.setupEtagCmds(device_info, "beijing_etag.json", 'http://192.168.2.103:6000/beijing')
    jsonFile = open('etag.json', 'w')
    json.dump(conf, jsonFile, ensure_ascii = False, indent = 2)
    cli.setupEtag(conf, '77')
    jsonFile.close()
    """
