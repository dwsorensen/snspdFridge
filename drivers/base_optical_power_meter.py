import baseinst


class dev(baseinst.dev):
    def get_power(self):
        return None

    def get_lambda(self):
        return None

    def set_lambda(self, value):
        return None

    def get_atim(self):
        return None

    def set_atim(self, value):
        return None

    def get_range(self):
        return None

    def set_range(self, value):
        return None

    def set_unit(self, value):
        return None

    def get_unit(self):
        return None

    def writeconfig(self, f):
        msg = self.identify()
        f.write(msg)
        wl = self.get_lambda()
        atim = self.get_atim()
        rng = self.get_range()
        if type(rng) == str:
            rang = rng
        else:
            rang = "%d" % rng
        f.write("# wavelength: %e\n# ATIM: %f\n# Range: %s\n" % (wl, atim, rang))
        f.flush()
