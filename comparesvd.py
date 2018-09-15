#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  3 10:33:35 2018

@author: burrbull
"""
import os
import xml.etree.ElementTree as ET
from openpyxl import Workbook, load_workbook

syns = {
		"ADC_Common" : "ADC",
		"DAC2" : "DAC",
		"Ethernet" : "ETHERNET",
		"Flash" : "FLASH",
		"SAI1" : "SAI",
		"TIMs" : "TIM",
		"USB_OTG" : "USB_OTG_FS",
		"USB_FS" : "USB",
		"DSIHOST" : "DSI",
		}
def gr_name(name):
	return syns[name] if name in syns else name


pth = os.getcwd()+"/"

devices = {
	"F0" : ["STM32F0x0", "STM32F0x1", "STM32F0x2", "STM32F0x8"],
	"F1" : ["STM32F100",  "STM32F101",  "STM32F102",  "STM32F103",  "STM32F107"],
	"F2" : ["STM32F215", "STM32F217",],
	"F3" : ["STM32F301", "STM32F302", "STM32F303", "STM32F373", "STM32F3x4", "STM32F3x8", ],
	"F4" : ["STM32F401", "STM32F405", "STM32F407", "STM32F410", "STM32F411", "STM32F412",
		 "STM32F413", "STM32F427", "STM32F429", "STM32F446", "STM32F469", ],
	"F7" : ["STM32F7x2", "STM32F7x3", "STM32F7x5", "STM32F7x6", "STM32F7x7", "STM32F7x9",],
	#"H7" : ["STM32H7x3",],
	"L0" : ["STM32L0x1", "STM32L0x2", "STM32L0x3",],
	"L1" : ["STM32L100", "STM32L151", "STM32L162",],
	"L4" : ["STM32L4x1", "STM32L4x2", "STM32L4x3", "STM32L4x5", "STM32L4x6",],
	"L4+" : ["STM32L4R5", "STM32L4R7", "STM32L4R9","STM32L4S5", "STM32L4S7", "STM32L4S9",],
	#"F103" : ["STM32F103xx_enum"],
}
devices["All"] = sum(devices.values(),[])
devices["F"] = sum([devices[k] for k in ["F0","F1","F2","F3","F4","F7"]],[])
devices["L"] = sum([devices[k] for k in ["L0","L1","L4"]],[])

from hashlib import blake2b

def get_registers(p):
	string = ET.tostring(p.find("registers"),encoding="utf-8")
	h = blake2b(digest_size=10)
	h.update(string)
	return h.hexdigest(), string
	#return hash(string), string

def compare_svd(grname, same=True, excelOnly=False):
	pdict = {}
	for fname in devices[grname]:
		etree = ET.parse(pth+fname+".svd")
		
		a = etree.find("peripherals")
		
		for p in a.iter("peripheral"):
			nm = p.find("name")
			printed = "{} {}".format(fname, nm.text)
			short_name = fname.replace("STM32", "")
			newfname = "{}.{}".format(nm.text, short_name)
			sameperiphs = ""
			if 'derivedFrom' in p.attrib:
				printed = "- "+printed
			else:
				groupName = gr_name(p.find("groupName").text)
				fpath = pth+grname+"/"+groupName
				if groupName not in pdict: # создать группу (ADC, SPI и т.д.)
					pdict[groupName] = {}
				 # вырезать регистры
				hsh, string = get_registers(p)
				if hsh in pdict[groupName]:
					pdict[groupName][hsh].append(newfname)
					printed = "  "+printed
				else:
					printed = "* "+printed
					pdict[groupName][hsh] = [newfname]
					groupName = gr_name(p.find("groupName").text)
					rt = ET.ElementTree(p.find("registers"))
					if not excelOnly:
						if not os.path.exists(fpath):
							os.makedirs(fpath)
						rt.write("{}/{}_{}.xml".format(fpath, groupName, hsh))
				sameperiphs += "{:20} -> {}.{}\n".format(str(hsh), short_name, nm.text)
				p.remove(p.find("registers"))
				h = ET.Element("hash")
				h.text = str(hsh)
				p.append(h)
			if same and (not excelOnly):
				if not os.path.exists(fpath):
					os.makedirs(fpath)
				with open("{}/sameperiphs.txt".format(fpath), "a") as f:
					f.write(sameperiphs)
			print(printed)
		if not excelOnly:
			etree.write("{}/{}.xml".format(pth+grname,fname))
	
	import pandas as pd
	
	d = [[per, str(h) , ", ".join(v)] for per in pdict for h, v in pdict[per].items()]
	#print(d)
	df = pd.DataFrame(d)
	excelname = pth+grname+'.xlsx'
	df.to_excel(excelname)

def compare_svds(ids, same=True, excelOnly=False):
	wb = Workbook()
	for k in ids:
		compare_svd(k, same, excelOnly)
		rows = reader(pth+k+'.xlsx')
		sheet = wb.create_sheet(k)
		for row in rows:
			sheet.append(row)
		os.remove(pth+k+'.xlsx')
		if same and (not excelOnly):
			for dirpath, _, filenames in os.walk(pth+k+'/'):
				if "sameperiphs.txt" in filenames:
					os.system('sort -o {0} {0}'.format(dirpath+"/sameperiphs.txt"))
	wb.save(pth+"Peripherals.xlsx")
	
	
def reader(file):
	wb_sheet = load_workbook(file).active
	rows = []
	for row in wb_sheet.iter_rows():
		row_data = []
		for cell in row:
			row_data.append(cell.value)
			rows.append(row_data)
	return rows

def restore_svd(fpath, infile, outpath, patch=True):
	print(infile)
	etree = ET.parse(fpath+infile+'.xml')
	a = etree.find("peripherals")
	for p in a.iter("peripheral"):
		if 'derivedFrom' in p.attrib:
			pass
		else:
			groupName = gr_name(p.find("groupName").text)
			h = p.find("hash")
			hsh = h.text
			print("  ", groupName, hsh)
			p.remove(h)
			rtree = ET.parse("{0}{1}/{1}_{2}.xml".format(fpath, groupName, hsh))
			r = rtree.getroot()
			p.append(r)
	tmp = outpath+infile+".svd"
	etree.write(tmp)
	os.system('xmllint --format "{0}{1}.svd" --output "{0}{1}.svd"'.format(outpath, infile))
	if patch:
		os.system('patch "{0}{1}.svd" "{0}patches/{1}.patch"'.format(outpath, infile))
	os.system('unix2dos "{0}{1}.svd"'.format(outpath, infile))

def restore_svds(gr, patch=True):
	for d in devices[gr]:
		restore_svd(pth+gr+"/", d, pth, patch)

def diff(fpath, groupName, ls=[]):
	import itertools
	fpath = fpath+groupName+"/"
	lst = [f for f in os.listdir(fpath) if f.endswith(".xml")]
	s = ""
	for f1, f2 in itertools.combinations(lst, 2):
		s += ("\n#############################"
			"### {} -> {} ###\n\n".format(f1, f2)
			)
		t = os.popen("diff -u3 {0}{1} {0}{2}".format(fpath, f1, f2))
		ss = t.read()
		s += ss
		s += "\n\n\n"
		ls.append([groupName, f1, f2, len(ss)])
	if len(lst) > 1:
		with open("{}{}_diff.txt", "w".format(fpath, groupName)) as f:
			f.write(s)

def diff_svds(folder):
	fpath = pth+folder+"/"
	lst = []
	for gr in os.listdir(fpath):
		if os.path.isdir(fpath+gr):
			diff(fpath, gr, lst)
	lst = sorted(lst, key = lambda r: (r[0], r[3]))
	for row in lst:
		s = " meld {0}/{1} {0}/{2}".format(row[0], row[1], row[2])
		row.append(s)
	import pandas as pd
	df = pd.DataFrame(lst)
	excelname = pth+"Diffs.xlsx"
	df.to_excel(excelname)

def sort_svd(grname):
	fpath = pth+"sorted/"
		
	for fname in devices[grname]:
		sort_single(pth, fpath, fname)
		
def sort_single(inpath, outpath, fname, down=True):
	if not os.path.exists(outpath):
		os.makedirs(outpath)
	print(fname)
	etree = ET.parse(inpath+fname+".svd")
	
	pp = etree.find("peripherals")

	for p in pp.iter("peripheral"):
		print("\t"+p.findtext("name"))
		if 'derivedFrom' in p.attrib:
			continue
		rr = p.find("registers")
		sort_registers(rr)
		
		for r in rr.iter("register"):
			ff = r.find("fields")
			sort_fields(ff, down)
		
		for c in rr.iter("cluster"):
			#sort_registers(c)
			for r in c.iter("register"):
				ff = r.find("fields")
				sort_fields(ff, down)
	etree.write(outpath+fname+".svd", encoding="utf-8")
	os.system('xmllint --format "{0}{1}.svd" --output "{0}{1}.svd"'.format(outpath, fname))
	os.system('patch "{0}{1}.svd" "{0}/../patches/{1}.patch"'.format(outpath, fname))
	os.system('unix2dos "{0}{1}.svd"'.format(outpath, fname))


def sort_fields(ff, down=True):
	if ff:
		fields = []
		for f in ff:
			key = int(f.findtext("bitOffset"))
			fields.append((key, f))
		#print(fields)
		if down:
			fields.sort(reverse=True, key=lambda x: x[0])
		else:
			fields.sort(key=lambda x: x[0])
		ff[:] = [item[-1] for item in fields]
		
def sort_registers(rr):
	if rr:
		registers = []
		for r in rr:
		#	print(r.find("name").text)
			txt = r.findtext("addressOffset")
			#print(txt)
			key = int(txt, 16)
			registers.append((key, r))
		registers.sort(key=lambda x: x[0])
		rr[:] = [item[-1] for item in registers]

def make_patches(gr):
	for d in devices[gr]:
		forig = pth+"orig/"+d+".svd"
		fnew = pth+d+".svd"
		fpatch = pth+"patches/"+d+".patch"
		s = 'diff -u3 "{}" "{}"'.format(fnew, forig)
		t = os.popen(s)
		st = t.read()
		with open(fpatch, "w") as f:
			f.write(st)


def svd_statistics(grname):
	for fname in devices[grname]:
		etree = ET.parse(pth+fname+".svd")
		
		a = etree.find("peripherals")
		print(fname, len(a.findall("peripheral")))
		#for p in a.iter("peripheral"):
		#	print(p)

def table_from_register(r):
	s = TABLEHEADER+"<h3>{}</h3>\n".format(r.findtext("name"))
	d = {}
	ff = r.find("fields")
	if not ff:
		return s
	for f in ff.iter("field"):
		d[int(f.findtext("bitOffset"))] = (f.findtext("name"),int(f.findtext("bitWidth")))
	pr_offset = 32
	high = ""
	low = ""
	for offset in sorted(d, reverse = True):
		name = d[offset][0]
		bw = d[offset][1]
		start = offset+bw
		if offset > 15:
			high += '<td class="reserved"></td>'*(pr_offset-start)
			high += '<td colspan="{}">{}</td>'.format(bw, name)
		elif start > 16:
			high += '<td class="reserved"></td>'*(pr_offset-start)
			high += '<td class="separated" colspan="{}">{}</td>'.format(start-16, name)
			low += '<td class="separated" colspan="{}">{}</td>'.format(16-offset, name)
		else:
			if pr_offset>16:
				high += '<td class="reserved"></td>'*(pr_offset-16)
				pr_offset = 16
			low += '<td class="reserved"></td>'*(pr_offset-start)
			low += '<td colspan="{}">{}</td>'.format(bw, name)
		pr_offset = offset
	if pr_offset > 0:
		if pr_offset>16:
			high += '<td class="reserved"></td>'*(pr_offset-16)
			pr_offset = 16
		low += '<td class="reserved"></td>'*(pr_offset)
	return s+"<tr>"+high+"""</tr>
  <tr>
    <td>31</td><td>30</td><td>29</td><td>28</td><td>27</td><td>26</td>
    <td>25</td><td>24</td><td>23</td><td>22</td><td>21</td><td>20</td>
    <td>19</td><td>18</td><td>17</td><td>16</td>
  </tr>
  <tr>
    <td colspan="16"></td>
  </tr>
  <tr>"""+low+"""</tr>
  <tr>
    <td>15</td><td>14</td><td>13</td><td>12</td><td>11</td><td>10</td>
    <td>9</td><td>8</td><td>7</td><td>6</td><td>5</td><td>4</td>
    <td>3</td><td>2</td><td>1</td><td>0</td>
  </tr>
</table>"""

TABLEHEADER = """<table class="tg">
<colgroup>
<col><col><col><col><col><col><col><col><col><col><col><col><col><col><col><col>
</colgroup>
"""

HEADER = """<html>
<body>
<style type="text/css">
.tg  {border-collapse:collapse;border-spacing:0;word-wrap: break-word;}
.tg td{font-family:Arial,sans-serif;font-size:13px;padding:10px 5px;border-style:solid;border-width:1px;border-color:black;text-align:center;vertical-align:center}
.tg col{width: 51px}
.tg td.reserved{font-size:11px;color:lightgrey}
.tg td.reserved:before {content: "Res."}
.tg td.separated{background-color:lightgrey}
nav a{display: block;}
</style>
"""

FOOTER = """
</body>
<html>
"""

def tables_from_svd(inpath, fname):
	print(fname)
	etree = ET.parse(inpath+fname+".svd")
	menu = "<nav>"
	pp = etree.find("peripherals")
	s = ""
	for p in pp.iter("peripheral"):
		pername = p.findtext("name")
		print("\t"+pername)
		if 'derivedFrom' in p.attrib:
			continue
		menu += '<a href="#{0}">{0}</a>'.format(pername)
		s += '<a name="{0}"></a><h2>{0}</h2>'.format(pername)
		rr = p.find("registers")
		
		for r in rr.iter("register"):
			s += table_from_register(r)
		
		for c in rr.iter("cluster"):
			s += "<h3>{}</h3>".format(c.findtext("name"))
			#sort_registers(c)
			for r in c.iter("register"):
				s += table_from_register(r)
	menu += "</nav>"
	with open("{}/{}.html".format(inpath,fname), "w") as f:
		f.write(HEADER+"<h1>{}</h1>\n".format(fname)+menu+s+FOOTER)