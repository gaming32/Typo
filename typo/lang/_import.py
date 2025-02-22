import sys, os
from ._core import verbose, run_script
import mimetypes, json
mimetypes.add_type('text/python', '.py')
mimetypes.add_type('text/typo-script', '.typ')
mimetypes.add_type('text/json', '.json')
from . import register_import

_pkgdir =  '/'.join(__file__.split(os.sep)[:-3])
import_dirs = ['.', _pkgdir+'/modules']

def import_typ(self, file):
    tkn, prs = __init__.run_script(file)
    self.vars.update(prs.vars)
    verbose('successfully imported from', file)
    verbose('\t', 'vars =>', prs.vars)
def import_py(self, file):
    path = os.path.split(file)
    path = (path[0], os.path.splitext(path[-1])[0])
    sys.path.insert(0, path[0])
    __import__(path[1])._call_typo_func = (lambda *cmd: self.run(*cmd))
    sys.path[:1] = []
    self.funcs.update(register_import.funcs)
    self.vars.update(register_import.vars)
    verbose('successfully imported from', file)
    verbose('\t', 'vars  =>', register_import.vars)
    verbose('\t', 'funcs =>', register_import.funcs)
    register_import.funcs = {}
    register_import.vars = {}

def _import_json_funcs(self, mod):
    funcs = {}
    for funcname in mod['functions']:
        func = mod['functions'][funcname]
        module = __import__(func['module'])
        del func['module']
        func['func'] = getattr(module, func['function'])
        del func['function']
        funcs[funcname] = func
    self.funcs.update(funcs)
    return funcs
def _import_json_vars(self, mod):
    vars = {}
    for varname in mod['vars']:
        var = mod['vars'][varname]
        module = __import__(var['module'])
        value = getattr(module, var['name'])
        vars[varname] = value
    self.vars.update(vars)
    return vars
def _import_json_dependencies(self, mod):
    for varname in mod['vars']:
        var = {
            "dependencies" : [],
            "default" : ""
        }
        var.update(mod['vars'][varname])
        mod['dependencies'] += var['dependencies']
        del var['dependencies']
        mod['vars'][varname] = var
    for funcname in mod['functions']:
        func = {
            "dependencies" : [],
            "maxargcount" : None,
            "defaults" : []
        }
        func.update(mod['functions'][funcname])
        mod['dependencies'] += func['dependencies']
        del func['dependencies']
        mod['functions'][funcname] = func
    for dependency in mod['dependencies']:
        __import__(dependency)
def import_json(self, file):
    mod = {
        "dependencies" : [],
        "functions" : {},
        "vars": {},
        "rawvars" : {}
    }
    mod.update(json.load(open(file)))
    _import_json_dependencies(self, mod)
    funcs = _import_json_funcs(self, mod)
    vars = _import_json_vars(self, mod)
    rawvars = mod['rawvars']
    self.vars.update(rawvars)
    verbose('successfully imported from', file)
    verbose('\t', 'funcs   =>', funcs)
    verbose('\t', 'vars    =>', vars)
    verbose('\t', 'rawvars =>', rawvars)

def import_file(self, file):
    ftype, archived = mimetypes.guess_type(file)
    if archived is not None: raise parse_error('attempted to import archived file')
    main, sub = ftype.split('/', 1)
    if main != 'text': raise parse_error('attempted to import non-text file')
    if sub == 'python': import_py(self, file)
    elif sub == 'typo-script': import_typ(self, file)
    elif sub == 'json': import_json(self, file)
    else: raise parse_error('unsupported file type for importing: %s' % ftype)
def import_(self):
    self.check_argcount(1)
    name = self.args[0]
    for impdir in self.modsearchlist:
        for ext in ('.py', '.typ', '.json'):
            file = os.path.join(impdir, name) + ext
            if os.path.isfile(file):
                try: import_file(self, file)
                except parse_error: pass
                else: return