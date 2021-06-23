from django import dispatch


class Signal(dispatch.Signal):
    def redirect(self, inst, **kwargs):
        del kwargs['signal']
        del kwargs['sender']
        self.send(instance=inst, sender=type(inst), **kwargs)
