import baseinst


class dev(baseinst.dev):
    def get_route(self):
        return None

    def set_route(self):
        return None

    def writeconfig(self, f):
        msg = self.identify()
        f.write(msg)
        route = self.get_route()
        f.write("# route: %d\n" % (route))
        f.flush()
