## This imports all of the modules in this folder that have an "identify" method
#import importlib
#import pkgutil
#
#for _, modname, _ in pkgutil.walk_packages(path=__path__,
#                                           prefix=__name__ + '.'):
#    _temp = importlib.import_module(modname)
#    for k, v in _temp.__dict__.items():
#        if k[0] != '_' and type(v) is type:
#            globals()[k] = v