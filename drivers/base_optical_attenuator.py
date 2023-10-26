import baseinst


class dev(baseinst.dev):
    def get_att(self):
        return None

    def set_att(self, value):
        return None

    def get_lambda(self):
        return None

    def set_lambda(self, value):
        return None

    def enable(self):
        return None

    def disable(self):
        return None

    def writeconfig(self, f):
        msg = self.identify()
        f.write(msg)
        wl = self.get_lambda()
        att = self.get_att()
        f.write("# wavelength: %e\n# Power: %d\n" % (wl, att))
        f.flush()
