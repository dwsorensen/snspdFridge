#%% Calculate CPW L and C

# % Note: Needs to be adapted to include ground plane, especially for very
# % wide resonators
# %

def _cpw_LC_per_meter_thick(width, gap, thickness, eps_r):
    from scipy.special import ellipk
    from numpy import log10, log
    """ Calculates L and C per meter of a coplanar waveguide with no ground plane,
        air above the CPW and a dielectric below with permittivity eps_r
    #%  =========|     |======|     |=========  / \
    #%  =========|     |======|     |=========   |  electrode thickness
    #%  =========|     |======|     |=========  \ /
    #%            <---><------><--->
    #%              gap  width  gap
    # From Jiansong Gao's 2008 Caltech Thesis  "The Physics of Superconducting Microwave Resonators"
    # chapter 3 (eqns 3.27 thru 3.31)
    """
    e0 = 8.85e-12
    u0 = 4*np.pi*1e-7
    
    
    a = width/2
    b = width/2 + gap
    d = 2*thickness/np.pi
    u1 = a + d/2 + 3/2*log(2)*d - d/2*log(d/a) + (d/2)*log((b-a)/(b+a))
    u2 = b - d/2 - 3/2*log(2)*d + d/2*log(d/b) - (d/2)*log((b-a)/(b+a))
    
    k = a/b
    kp = np.sqrt(1-k**2)
    kt = u1/u2
    kpt = np.sqrt(1-kt**2)
    
    C = 2*e0*ellipk(kt)/ellipk(kpt) + 2*eps_r*e0*ellipk(k)/ellipk(kp)
    
    # Recalculate 3.27 with half-thickness to get total inductance as in 3.31
    a = width/2
    b = width/2 + gap
    d = 2*thickness/np.pi / 2 # half-thickness
    u1 = a + d/2 + 3/2*log(2)*d - d/2*log(d/a) + (d/2)*log((b-a)/(b+a))
    u2 = b - d/2 - 3/2*log(2)*d + d/2*log(d/b) - (d/2)*log((b-a)/(b+a))
    
    k = a/b
    kp = np.sqrt(1-k**2)
    kt = u1/u2
    kpt = np.sqrt(1-kt**2)
    
    L = u0/4*ellipk(kpt)/ellipk(kt)
    
    
    return L,C

def _cpw_LC_per_meter(width, gap, eps_eff):
    from scipy.special import ellipk
    from numpy import log10, log
    """ Calculates L and C per meter of a coplanar waveguide with no ground plane,
        and infinitely thin electrode metal
        (eps_eff = average of relative permittivities of dielectric above and
        below, for example if vacuum above + silicon below eps_eff = (1+11)/2 = 6)
    #%  =========|     |======|     |=========
    #%            <---><------><--->
    #%              gap  width  gap
    # From Jiansong Gao's 2008 Caltech Thesis  "The Physics of Superconducting Microwave Resonators"
    # chapter 3 (eqns 3.17 thru 3.20)
    """
    e0 = 8.85e-12
    u0 = 4*np.pi*1e-7
    
    
    a = width/2
    b = width/2 + gap
    k = a/b
    kp = np.sqrt(1-k**2)
    
    C = eps_eff*e0*4*ellipk(k)/ellipk(kp)
    L = u0/4*ellipk(kp)/ellipk(k)
    
    return L,C


def cpw_LC_with_Lk(width, gap, thickness, eps_eff, Lk_per_sq = 250e-12):
    L,C = cpw_LC_per_meter(width, gap, thickness, eps_eff)
    L += Lk_per_sq/width
    return L,C

# L,C = _cpw_LC_per_meter(width = 50e-6, gap = 5e-6, thickness = 4e-9, eps_r = 12.9, Lk_per_sq = 250e-12)
# Z = np.sqrt(L/C)
# v = np.sqrt(1/(L*C))
# print(Z)


def _cpw_Z_with_Lk(wire_width, gap, eps_eff, Lk_per_sq):
    # Add a kinetic inductance and recalculate the impedance, be careful
    # to input Lk as a per-meter inductance

    L_m, C_m = _cpw_LC_per_meter(wire_width, gap, eps_eff)
    Lk_m = Lk_per_sq*(1.0/wire_width)
    Z = np.sqrt((L_m+Lk_m)/C_m)
    return Z

def _cpw_v_with_Lk(wire_width, gap, eps_eff, Lk_per_sq):
    L_m, C_m = _cpw_LC_per_meter(wire_width, gap, eps_eff)
    Lk_m = Lk_per_sq*(1.0/wire_width)
    v = 1/np.sqrt((L_m+Lk_m)*C_m)
    return v



def _find_cpw_wire_width(Z_target, gap, eps_eff, Lk_per_sq):

    def error_fun(wire_width):
        Z_guessed = _cpw_Z_with_Lk(wire_width, gap, eps_eff, Lk_per_sq)
        return (Z_guessed-Z_target)**2 # The error

    x0 = gap
    try:
        from scipy.optimize import fmin
    except:
        raise ImportError(""" [PHIDL] To run the microsctrip functions you need scipy,
          please install it with `pip install scipy` """)
    w = fmin(error_fun, x0, args=(), disp=False)
    return w[0]