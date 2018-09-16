import os
import xml.etree.ElementTree as ET

pth = os.getcwd()+"/"

from devicedict import devices

def short_access(a):
	d = {"read-write": "rw", "read-only" : "r", "write-only" :"w"}
	return d.get(a, "N/A")

def table_from_register(r, coffset=None):
	name = r.findtext("name")
	dimIndex = r.findtext("dimIndex")
	dimIndex = "["+dimIndex+"]" if dimIndex else ""
	dim = int(r.findtext("dim") or "1")
	dimIncrement = r.findtext("dimIncrement")
	roffset = r.findtext("addressOffset")
	if dim != 1:
		roffset = "{} + [0-{}]*{}".format(roffset, dim-1, dimIncrement)
	if coffset:
		roffset = "{} + {}".format(coffset, roffset)
	name = name.replace("%s",dimIndex)
	resetValue = r.findtext("resetValue")
	s = TABLEHEADER+"<h3>{}</h3>\n<p>Address offset: {}</p><p>Reset value: {}</p>\n".format(name,roffset,resetValue)
	d = {}
	raccess = r.findtext("access")
	ff = r.find("fields")
	if not ff:
		return s
	for f in ff.iter("field"):
		d[int(f.findtext("bitOffset"))] = (f.findtext("name"),int(f.findtext("bitWidth")),short_access(f.findtext("access") or raccess or ""))
	pr_offset = 32
	high = ""
	low = ""
	for offset in sorted(d, reverse = True):
		name = d[offset][0]
		bw = d[offset][1]
		access = d[offset][2]
		start = offset+bw
		if offset > 15:
			high += '<td class="reserved"></td>'*(pr_offset-start)
			high += '<td colspan="{}">{}<br>{}</td>'.format(bw, name, access)
		elif start > 16:
			high += '<td class="reserved"></td>'*(pr_offset-start)
			high += '<td class="separated" colspan="{}">{}<br>{}</td>'.format(start-16, name, access)
			low += '<td class="separated" colspan="{}">{}<br>{}</td>'.format(16-offset, name, access)
		else:
			if pr_offset>16:
				high += '<td class="reserved"></td>'*(pr_offset-16)
				pr_offset = 16
			low += '<td class="reserved"></td>'*(pr_offset-start)
			low += '<td colspan="{}">{}<br>{}</td>'.format(bw, name, access)
		pr_offset = offset
	if pr_offset > 0:
		if pr_offset>16:
			high += '<td class="reserved"></td>'*(pr_offset-16)
			pr_offset = 16
		low += '<td class="reserved"></td>'*(pr_offset)
	return s+"""<tr class="number">
    <td>31</td><td>30</td><td>29</td><td>28</td><td>27</td><td>26</td>
    <td>25</td><td>24</td><td>23</td><td>22</td><td>21</td><td>20</td>
    <td>19</td><td>18</td><td>17</td><td>16</td>
  </tr>
  <tr>"""+high+"""</tr>
  <tr class="space">
    <td colspan="16"></td>
  </tr>
  <tr class="number">
    <td>15</td><td>14</td><td>13</td><td>12</td><td>11</td><td>10</td>
    <td>9</td><td>8</td><td>7</td><td>6</td><td>5</td><td>4</td>
    <td>3</td><td>2</td><td>1</td><td>0</td>
  </tr>
  <tr>"""+low+"""</tr>
</table>"""

def tables_from_peripheral(p):
	s = ""
	pername = p.findtext("name")
	s += '<a name="{0}"></a><h2>{0}</h2>'.format(pername)
	rr = p.find("registers")
	
	for r in rr.iter("register"):
		s += table_from_register(r)
	
	for c in rr.iter("cluster"):
		cname = c.findtext("name")
		dimIndex = c.findtext("dimIndex")
		dimIndex = "["+dimIndex+"]" if dimIndex else ""
		dim = int(c.findtext("dim") or "1")
		dimIncrement = c.findtext("dimIncrement")
		coffset = c.findtext("addressOffset")
		if dim != 1:
			coffset = "{} + [0-{}]*{}".format(coffset, dim-1, dimIncrement)
		cname = cname.replace("%s",dimIndex)
		s += '<h3 class="cluster">{}</h3>'.format(cname)
		#sort_registers(c)
		for r in c.iter("register"):
			s += table_from_register(r, coffset)
	return s


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
.tg tr.number td,.tg tr.space td{border-style:none}
.tg col{width: 51px}
.tg td.reserved{font-size:11px;color:lightgrey}
.tg td.reserved:before {content: "Res."}
.tg td.separated{background-color:lightgrey}
nav a{display: block;}
h2 {color:green}
h3.cluster {color:blue}
h3.cluster::before {content:"cluster "}
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
		menu += '<a href="#{0}">{0}</a>'.format(pername)
		print("\t"+pername)
		if 'derivedFrom' in p.attrib:
			continue
		s += tables_from_peripheral(p)
	menu += "</nav>"
	with open("{}/{}.html".format(inpath,fname), "w") as f:
		f.write(HEADER+"<h1>{}</h1>\n".format(fname)+menu+s+FOOTER)