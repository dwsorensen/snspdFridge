import baseinst


class dev(baseinst.dev):
    def get_power(self):
        return None

    def set_power(self):
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
        power = self.get_power()
        f.write("# wavelength: %e\n# Power: %e\n" % (wl, power))
        f.flush()
