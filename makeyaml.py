def make_yaml(fromfile, outdir):
	fullml = {}
	fromtree = ET.parse(fromfile)
	pp= fromtree.find("peripherals")
	for p in pp.iter("peripheral"):
		pname = p.findtext("name")
		if 'derivedFrom' in p.attrib:
			continue
		ppath = SvdPath.from_str(pname)
		rr = p.find("registers")
		pml = registers_yaml(rr, ppath, pp)
		for c in rr.iter("cluster"):
			cname = c.findtext("name")
			cml = registers_yaml(c, ppath+cname, pp)
			if cml:
				pml[":"+cname.replace("%s", "*")] = cml
		if pml:
			fullml[pname] = pml
	save_yaml(fullml, outdir)

def save_yaml(fullml, outdir):
	import yaml
	for pname, pml in fullml.items():
		filename = "{}/{}.yaml".format(outdir, pname)
		with open(filename, "w") as f:
			f.write(yaml.dump({pname:pml}))
	filename = "{}/{}.yaml".format(outdir, "lib")
	with open(filename, "w") as f:
		f.write("_include:\n"+"\n".join([f"- {pname}.yaml" for pname in fullml]))

def registers_yaml(rr, rrpath, pp):
	ml = {}
	for r in rr.iterfind("register"):
		rname = r.findtext("name")
		rml = register_yaml(r, rrpath+rname, pp)
		if rml:
			ml[rname.replace("%s", "*")] = rml
	return ml

def register_yaml(r, rpath, pp):
	rml = {}
	ff = r.find("fields")
	for f in ff.iter("field"):
		fname = f.findtext("name")
		fpath = rpath + fname
		wc = f.find("writeConstraint")
		evs = f.findall("enumeratedValues")
		if wc:
			rml[fname] = wc_yaml(wc)
		elif len(evs) == 1:
			dev = get_dev_yaml(evs[0], fpath, pp)
			if not dev:
				continue
			evml = ev_yaml(dev)
			if evml:
				rml[fname] = evml
		elif len(evs) > 1:
			evsml = {}
			for ev in evs:
				dev = get_dev_yaml(ev, fpath, pp)
				if not dev:
					continue
				evml = ev_yaml(dev)
				if evml:
					evsml["_"+dev.findtext("usage")] = evml
			if evsml:
				rml[fname] = evsml
	return rml

def get_dev_yaml(ev, fpath, pp):
	if 'derivedFrom' in ev.attrib:
		dpath = SvdPath.from_str(ev.attrib['derivedFrom'])
		dname = dpath[-1]
		if len(dpath) == 1:
			if len(fpath) == 4:
				dev = pp.find("peripheral[name='{}']/registers/cluster[name='{}']/register[name='{}']/fields/field/enumeratedValues[name='{}']".format(*fpath[:-1],dname))
			elif len(fpath) == 3:
				dev = pp.find("peripheral[name='{}']/registers/register[name='{}']/fields/field/enumeratedValues[name='{}']".format(*fpath[:-1],dname))
			else:
				dev = None
			if dev:
				return dev
			else:
				print("Can't find EV {} in path {}".format(*fpath[:-1],dname))
				return None
		else:
			if len(dpath)>3:
				fulldpath = list(dpath)
			else:
				fulldpath = SvdPath(fpath[:-(len(dpath)-1)]+dpath[:])
			if len(fulldpath) == 5:
				dev = pp.find("peripheral[name='{}']/registers/cluster[name='{}']/register[name='{}']/fields/field[name='{}']/enumeratedValues[name='{}']".format(*fulldpath))
			elif len(fulldpath) == 4:
				dev = pp.find("peripheral[name='{}']/registers/register[name='{}']/fields/field[name='{}']/enumeratedValues[name='{}']".format(*fulldpath))
			else:
				dev = None
			if dev:
				return dev
			else:
				print("Can't find EV {}:   {}   {}".format(fulldpath, fpath, dpath))
				return None
	else: return ev

def ev_yaml(ev):
	evml = {}
	for v in ev.iter("enumeratedValue"):
		evml[v.findtext("name")] = [int(v.findtext("value")), v.findtext("description")]
	return evml

def wc_yaml(wc):
	rng = wc.find("range")
	if rng:
		return [int(rng.findtext("minimum")), int(rng.findtext("maximum"))]
