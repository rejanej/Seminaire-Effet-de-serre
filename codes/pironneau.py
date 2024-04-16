'''
Code pour simuler l'effet de serre dans l'atmosphère
par transfert radiatif. Met à jour la température dans
l'atmosphère en fonction de l'absorption et de l'émission
de rayonnement.

'''

import numpy as np
import threading


class RadiativeTransferModel:

    # constantes et paramètres

    def __init__(self, MM, n, kmax, Z, SBsun, Tsun, numax, jmax, dnu0, dtt, nt, knu0, dknu, nu01, nu02, nu03, nu04, pi, anu):
        self.MM = MM
        self.n = n
        self.kmax = kmax
        self.Z = Z
        self.SBsun = SBsun
        self.Tsun = Tsun
        self.numax = numax
        self.jmax = jmax
        self.dnu0 = dnu0
        self.dtt = dtt
        self.nt = nt
        self.knu0 = knu0
        self.dknu = dknu
        self.nu01 = nu01
        self.nu02 = nu02
        self.nu03 = nu03
        self.nu04 = nu04
        self.pi = pi
        self.anu = anu
        self.alpha = [0.1]*5+ [0.0]*165 + [0.65]*7 + [0.0]*3
        self.alpha.reverse()

        self.Inut = np.zeros(self.MM) # mu intégrale de l'intensité lumineuse) sur l'ensemble des points de l'atmosphère
        self.F = np.zeros(self.MM) # valeurs des contributions aux intégrales
        self.T = np.zeros(self.MM) # température
        self.T1 = np.zeros(self.MM) # température scénario 1
        self.T2 = np.zeros(self.MM) # température scénario 2
        self.T3 = np.zeros(self.MM) # température scénario 3
        self.Aaux = np.zeros(self.MM) # calculs intermédiaires

    def expint_E1(self, t, B=1): # fonction qui calcule l'intégrale  E1(t)*B
        K = 8
        epst = 1e-5
        gamma = 0.577215664901533

        if t == 0:
            return -1e12 * B

        abst = np.abs(t)
        if abst < epst:
            return -abst * (gamma + np.log(abst) - 1) * B

        ak = abst
        somme = -gamma - np.log(abst) + ak

        for k in range(2, K): #intégrale trapèzes
            ak *= -abst * (k - 1) / (k**2)
            somme += ak

        return somme * B

    def Bsun(self, nu):  # focntion qui calcule la puissance solaire normalisée 
        return self.SBsun * nu**3 / (np.exp(nu / self.Tsun) - 1)

    def BB(self, nu, T): # fonction qui calcule la fonction de boltzmann 
        return nu**3 / (np.exp(nu / T) - 1)

    def intB(self, kappa, nu, tau, tmin, tmax): # fonction qui retourne l'intégrale de convolution de E1*B sur un intervalle donné
        aux = 0
        dt = min(self.dtt, self.nt / (tmax - tmin))

        for t in np.arange(tmin, tmax, dt): # intégrale
            baux = self.BB(nu, self.T[int((self.MM - 1) * t / self.Z)])
            if kappa * (t - tau) != 0:
                aux += dt * kappa * self.expint_E1(kappa * np.abs(tau - t), baux)

        return aux

    def getT(self, nu1, nu2, dknu): # maj de température dans l'atmosphère (loi de kirchhoff avec des corrections)
        for i in range(self.MM):
            Bik = self.F[i] / 2
            if dknu != 0:
                for nu in np.arange(nu1, nu2, self.dnu0):
                    Bik -= self.BB(nu, self.T[i]) * dknu * self.dnu0
            self.T[i] = np.sqrt(np.sqrt(abs(15 * Bik / self.knu0))) / self.pi

    def getInu(self, kappa, nu): # calcule l'intensité lumineuse I_nu 
        for i in range(self.MM):
            x = i * self.Z / (self.MM - 1) # altitude normalisée entre 0 et 1 
            self.Inut[i] = (
                self.intB(kappa, nu, x, 0, self.Z)
                + self.Bsun(nu) * (np.exp(-kappa * x) * (1 - kappa * x) + self.expint_E1(kappa * x, kappa * x**2)) / 2
                #+ (self.anu * kappa * self.Inut[i] )/2
                #-self.anu * self.intB(kappa, nu, x, 0, self.Z) 
            )
    
    def getInu2(self, kappa, nu, albedo_sol, albedos, altitudes):
        for i in range(self.MM):
            x = i * self.Z / (self.MM - 1)
            self.Inut[i] = (
                self.intB(kappa, nu, x, 0, self.Z)
                + self.Bsun(nu) * (np.exp(-kappa * x) * (1 - kappa * x) + self.expint_E1(kappa * x, kappa * x**2)) / 2
                + (self.anu * kappa * self.Inut[i]) / 2 - self.anu * self.intB(kappa, nu, x, 0, self.Z)
            )

            # Albedo nuage à une altitude spécifique
            # for altitude, albedo in zip(altitudes, albedos):
            #     if np.abs(x - altitude) < 1/24:
            #         self.Inut[i] += albedo * self.Inut[i] * np.exp(kappa * (x - self.Z))

            # # Albedo au sol
            # if x < 0.02:  # altitude moyenne globale de 250m (840m continentale et 0m océanique -> 0.3 * 840 =250)
            #     self.Inut[i] += albedo_sol * self.Inut[-1] * np.exp(kappa * (x - self.Z))


    def multiBlock2(self, nu1, nu2, dknu):
        albedo_sol = 0.15  # coeff albédo sol
        albedos = [0.5]  # coefficients albédo pour chaque altitude
        altitudes = [0.5]  # altitudes coefficients d'albédo : altitude de 3 km
        for i in range(self.MM):
            self.T[i] = 0.07
        
        for k in range(self.kmax):
            for i in range(self.MM):
                self.F[i] = 0
                self.Inut[i] = 0
            nu = 0
            for j in range(1, self.jmax + 1):
                dnu = (2 * j - 1) * self.dnu0
                nu += dnu
                kappa = self.knu0 + dknu * (nu > nu1) * (nu < nu2)
                for i in range(self.MM):
                    self.F[i] += kappa * self.Inut[i] * dnu / 2
                #self.getInu(kappa, nu)
                self.getInu2(kappa, nu, albedo_sol, albedos, altitudes)
                for i in range(self.MM):
                    self.F[i] += kappa * self.Inut[i] * dnu / 2

            self.getT(nu1, nu2, dknu)
            print(f"k= {k} {self.T[0]} {self.T[self.MM - self.n]}")



if __name__ == "__main__":
    MM = 180  # nombre de points d'altitude dans l'atmosphère
    n = 6  # paramètre de l'atmosphère
    kmax = 12  # nombre maximum d'itérations
    Z = 1 - np.exp(-12.0)  # hauteur totale de l'atmosphère (normalisée entre 0 et 1)
    SBsun = 3.042e-5  # puissance solaire rayonnée à la surface de l'étoile (constante de Stefan-Boltzmann pour le Soleil)
    Tsun = 1.209  # température de surface de l'étoile (en unités appropriées)
    numax = 20  # freq maximale
    jmax = 150  # nombre maximal de termes dans la sommation de l'intensité lumineuse
    dnu0 = numax / (jmax**2)  # incrément de fréquence pour la sommation de l'intensité lumineuse
    dtt = 0.005  # incrément de temps pour l'intégration temporelle
    nt = 5  # nombre de points pour l'intégration temporelle
    knu0 = 1.225  # coeff d'absorption initial
    dknu = -0.5  # variation du coefficient d'absorption
    nu01, nu02, nu03, nu04 = 0.2, 0.3, 0.1, 0.4  # fréquences pour différents scénarios
    pi = 4 * np.arctan(1.0)  # valeur de pi
    anu = 0.3  # albedo moyen de la Terre

    model = RadiativeTransferModel(MM, n, kmax, Z, SBsun, Tsun, numax, jmax, dnu0, dtt, nt, knu0, dknu, nu01, nu02, nu03, nu04, pi, anu)

    scenarios = [(model.nu01, model.nu02, 0.0), (model.nu01, model.nu02, model.dknu), (model.nu03, model.nu04, model.dknu)]

    # SCENARIO 1 : fréquence constante et coefficient d'absorption constant
    print("\n kappa constant \n iterations \t [T] near Earth and far near Z\n")
    model.multiBlock2(model.nu01, model.nu02, 0.0)
    model.T1[:] = model.T[:]

    # SCENARIO 2 :  fréquence variable (étroite) et variation coefficient d'absorption
    print("kappa variable\n iterations \t [T] near Earth and far near Z\n")
    model.multiBlock2(model.nu01, model.nu02, model.dknu)
    model.T2[:] = model.T[:]

    # SCENARIO 3 :  fréquence variable (large) et variation coefficient d'absorption
    print("kappa variable\n iterations \t [T] near Earth and far near Z\n")
    model.multiBlock2(model.nu03, model.nu04, model.dknu)
    model.T3[:] = model.T[:]

    print("\n tau\t \t [T1]:Milne [T2]:narrow [T3]:wide [T1-T2]/T [T2-T3]/T \n ")
    with open("results_init.txt", "w") as myfile: #s pécifier le nom du fichier à enregistrer ici

        for i in range(1, model.MM):
            print(
                -np.log(1 - i * model.Z / (model.MM - 1)),
                model.T1[i],
                model.T2[i],
                model.T3[i],
                2 * (model.T1[i] - model.T2[i]) / (model.T2[i] + model.T1[i]),
                2 * (model.T2[i] - model.T3[i]) / (model.T3[i] + model.T2[i]),
            )
            myfile.write(
                f"{-np.log(1 - i * model.Z / (model.MM - 1))}\t"
                f"{model.T1[i]}\t{model.T2[i]}\t{model.T3[i]}\t"
                f"{2 * (model.T2[i] - model.T1[i]) / (model.T2[i] + model.T1[i])}\t"
                f"{2 * (model.T1[i] - model.T3[i]) / (model.T1[i] + model.T3[i])}\t\n"
            )

