from happybudget.lib.utils import import_at_module_path


def instantiate_permissions(ps):
    ps = [import_at_module_path(p) if isinstance(p, str) else p for p in ps]
    return [p() if isinstance(p, type) else p for p in ps]
