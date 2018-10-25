# =====================================================================================================
# 7-PARAMETRICNA TRANSFORMACIJA MED D48/GK IN D96/TM
# =====================================================================================================

import math
from numpy import matrix

def main():

	# -------------------------------------------------------------------------------------------------
	# Vhodne koordinate v D48/GK
	# -------------------------------------------------------------------------------------------------
	y = 500000
	x = 100000
	H = 100
	print 'Ravninske modulirane koord. v D48/GK:', y, x, H

	# -------------------------------------------------------------------------------------------------
	# D48/GK
	# -------------------------------------------------------------------------------------------------
	# Besselov elipsoid
	a = 6377397.15500
	b = 6356078.96325
	# GK projekcija
	m0 = 0.9999		# linijsko merilo na srednjem meridianu
	fx = -5000000	# false northing
	fy = 500000		# false easting
	la0 = 15		# centralni meridian

	e = math.sqrt((a**2-b**2)/a**2)			# prva ekscentricnost
	ee = math.sqrt((a**2-b**2)/b**2)		# druga ekscentricnost

	# -------------------------------------------------------------------------------------------------
	# D96/TM
	# -------------------------------------------------------------------------------------------------
	# GRS80
	a2 = 6378137.00000
	b2 = 6356752.31414
	# TM projekcija
	m02 = 0.9999
	fN = -5000000
	fE = 500000
	la02 = 15
	
	e2 = math.sqrt((a2**2-b2**2)/a2**2)			
	ee2 = math.sqrt((a2**2-b2**2)/b2**2)
	
	# =================================================================================================
	# PRETVORBA RAVNINSKIH KOORDINAT V ELIPSOIDNE: (y,x) -> (la, fi)
	# =================================================================================================
	
	# Demodulacija
	ym = (y - fy)/m0
	xm = (x - fx)/m0			
	
	print 'Ravninske nemodulirane koord. v D48/GK:', ym, xm, H
	
	# -------------------------------------------------------------------------------------------------
	# izracun fi1 -> geogr. sirina vznozisca tocke (footpoint latitude), pri kateri je L = xm
	# -------------------------------------------------------------------------------------------------
	
	# Prvi priblizek
	fi0 = 2*xm/(a+b)
	
	# Dolzina loka meridiana od ekvatorja do dane geogr. sirine
	A = 1 + 3/4.*e**2 + 45/64.*e**4 + 175/256.*e**6 + 11025/16384.*e**8 + 43659/65536.*e**10
	B = 3/4.*e**2 + 15/16.*e**4 + 525/512.*e**6 + 2205/2048.*e**8 + 72765/65536.*e**10
	C = 15/64.*e**4 + 105/256.*e**6 + 2205/4096.*e**8 + 10395/16384.*e**10
	D = 35/512.*e**6 + 315/2048.*e**8 + 31185/131072.*e**10
	E = 315/16384.*e**8 + 3465/65536.*e**10
	F = 693/131072.*e**10
	
	L = a*(1-e**2)*(A*fi0 - B*math.sin(2*fi0)/2. + C*math.sin(4*fi0)/4. \
		- D*math.sin(6*fi0)/6. + E*math.sin(8*fi0)/8. \
		- F*math.sin(10*fi0)/10.)
	
	# Razlika med dolzino loka meridiana (L) in modulirano koordinato x (xm)
	d1 = xm - L	
	
	# Drugi priblizek	
	fi1 = fi0 + 2*d1/(a + b)
	
	# Iteracija (postopek se ustavi, ko je razlika d1 < 0.000001 m)
	while d1 > 0.000001:
		fi0 = fi1
		#print math.degrees(fi1)
		L = a*(1-e**2)*(A*fi0 - B*math.sin(2*fi0)/2. + C*math.sin(4*fi0)/4. \
			- D*math.sin(6*fi0)/6. + E*math.sin(8*fi0)/8. \
			- F*math.sin(10*fi0)/10.)
		d1 = xm - L
		fi1 = fi0 + 2*d1/(a+b)
				
	# -------------------------------------------------------------------------------------------------
	# Izracun geografske dolzine in geografske sirine tocke
	# -------------------------------------------------------------------------------------------------
	
	# Polmer ukrivljenosti prvega vertikala
	N = a/math.sqrt(1-(e**2)*(math.sin(fi1)**2))
	
	# Pomozne kolicine
	eta = ee*math.cos(fi1)
	cosFi = math.cos(fi1)
	tanFi = math.tan(fi1)
	
	# Izracun geogr. dolzine
	la = math.radians(la0) + ym/(N*cosFi) - ym**3*(1+2*tanFi**2+eta**2)/(6*N**3*cosFi) \
		+ ym**5*(5+28*tanFi**2+24*tanFi**4+6*eta**2+8*tanFi**2*eta**2)/(120*N**5*cosFi) \
		- ym**7*(61+662*tanFi**2+1320*tanFi**4+720*tanFi**6)/(5040*N**7*cosFi)
	
	# izracun geogr. sirine
	fi = fi1 - ym**2*tanFi*(1+eta**2)/(2*N**2) \
		+ ym**4*tanFi*(5+3*tanFi**2+6*eta**2-6*tanFi**2*eta**2-3*eta**4-9*tanFi**2*eta**4)/(24*N**4) \
		- ym**6*tanFi*(61+90*tanFi**2+45*tanFi**4+107*eta**2-162*tanFi**2*eta**2-45*tanFi**4*eta**2)/(720*N**6) \
		+ ym**8*tanFi*(1385+3633*tanFi**2+4095*tanFi**4+1575*tanFi**6)/(40320*N**8)
	
	# Visina
	h = H 

	print 'Geografske koord. na Besselu:', math.degrees(fi), math.degrees(la), h
	
	# =================================================================================================
	# PRETVORBA GEOGRAFSKIH KOORDINAT V KARTEZICNE: (fi,la, h) -> (X, Y, Z)
	# =================================================================================================
	
	# Polmer ukrivljenosti prvega vertikala
	N = a/math.sqrt(1-(e**2)*(math.sin(fi)**2))
	
	# Izracun kartezicnih koordinat
	X = (N + h)*math.cos(fi)*math.cos(la)
	Y = (N + h)*math.cos(fi)*math.sin(la)
	Z = ((1 - e**2)*N + h)*math.sin(fi)
	print 'Kartezicne koord. na Besselu:', X, Y, Z
	
	# =================================================================================================
	# HELMERTOVA TRANSFORMACIJA KARTEZICNIH KOORDINAT: (X, Y, Z) -> (X2, Y2, Z2)
	# =================================================================================================
	
	# Parametri za celo Slovenijo
	dX = 409.545
	dY = 72.164
	dZ = 486.872
	Rx = math.radians(-3.085957/3600.)	# v radianih
	Ry = math.radians(-5.46911/3600.)	# v radianih
	Rz = math.radians(11.020289/3600.)	# v radianih
	M = 17.919665/1000000.	
	
	# Rotacijska matrika
	R3 = matrix([[math.cos(Rz), math.sin(Rz), 0], \
				[-math.sin(Rz), math.cos(Rz), 0], \
				[0, 0, 1]])
	R2 = matrix([[math.cos(Ry), 0, -math.sin(Ry)], \
				[0, 1, 0], \
				[math.sin(Ry), 0, math.cos(Ry)]])
	R1 = matrix([[1, 0, 0], \
				[0, math.cos(Rx), math.sin(Rx)], \
				[0, -math.sin(Rx), math.cos(Rx)]])
	R = R3*R2*R1
		
	# Helmertova transformacija -> kartezicne koordinate v drugem koordinatnem sistemu
	Helmert = (1+M)*R*matrix([[X],[Y],[Z]])+matrix([[dX],[dY],[dZ]])
	
	X2 = Helmert.item(0)
	Y2 = Helmert.item(1)
	Z2 = Helmert.item(2)
	print 'Kartezicne koord. na GRS80:', X2, Y2, Z2
	
	# =================================================================================================
	# PRETVORBA KARTEZICNIH KOORDINAT V GEOGRAFSKE: (X, Y, Z) -> (fi,la, h)
	# =================================================================================================
	
	# Geografska dolzina
	la2 = math.atan(Y2/X2)
	
	# Geografska dolzina
	p = math.sqrt(X2**2+Y2**2)
	theta = math.atan((Z2*a2)/(p*b2))
	fi2 = math.atan((Z2+ee2**2*b2*math.sin(theta)**3)/(p-e2**2*a2*math.cos(theta)**3))
	
	# Elipsoidna visina
	N2 = a2/math.sqrt(1-e2**2*math.sin(fi2)**2)
	h2 = p/math.cos(fi2) - N2
		
	print 'Geografske koord. na GRS80:', math.degrees(fi2), math.degrees(la2), h2
	
	# =================================================================================================
	# PRETVORBA GEOGRAFSKIH KOORDINAT V RAVNINSKE: (fi,la, h) -> (E, N, H)
	# =================================================================================================
	
	# Pomozne kolicine
	eta2 = ee2*math.cos(fi2)
	cosFi2 = math.cos(fi2)
	tanFi2 = math.tan(fi2)
	dLa = la2 - math.radians(la02)
	
	# Dolzina loka meridiana od ekvatorja do dane geogr. sirine
	A2 = 1 + 3/4.*e2**2 + 45/64.*e2**4 + 175/256.*e2**6 + 11025/16384.*e2**8 + 43659/65536.*e2**10
	B2 = 3/4.*e2**2 + 15/16.*e2**4 + 525/512.*e2**6 + 2205/2048.*e2**8 + 72765/65536.*e2**10
	C2 = 15/64.*e2**4 + 105/256.*e2**6 + 2205/1096.*e2**8 + 10395/16384.*e2**10
	D2 = 35/512.*e2**6 + 315/2048.*e2**8 + 31185/131072.*e2**10
	E2 = 315/16384.*e2**8 + 3465/65536.*e2**10
	F2 = 693/131072.*e2**10

	L2 = a2*(1-e2**2)*(A2*fi2 - B2*math.sin(2*fi2)/2. + C2*math.sin(4*fi2)/4. \
		- D2*math.sin(6*fi2)/6. + E2*math.sin(8*fi2)/8. \
		- F2*math.sin(10*fi2)/10.)
	
	# -------------------------------------------------------------------------------------------------
	# Izracun ravninskih koordinat
	# -------------------------------------------------------------------------------------------------
	Em = N2*cosFi2*dLa + (N2*cosFi2**3*(1-tanFi2**2+eta2**2)*dLa**3)/6. \
		+ (N2*cosFi2**5*(5-18*tanFi2**2+tanFi2**4+14*eta2**2-58*tanFi2**2*eta2**2)*dLa**5)/120. \
		+ (N2*cosFi2**7*(61-479*tanFi2**2+179*tanFi2**4-tanFi2**6)*dLa**7)/5040.
	
	Nm = L2 + (N2*tanFi2*cosFi2**2*dLa**2)/2. \
		+ (N2*tanFi2*cosFi2**4*(5-tanFi2**2+9*eta2**2+4*eta2**4)*dLa**4)/24. \
		+ (N2*tanFi2*cosFi2**6*(61-58*tanFi2**2+tanFi2**4+270*eta2**2-330*tanFi2**2*eta2**2)*dLa**6)/720. \
		+ (N2*tanFi2*cosFi2**8*(1385-3111*tanFi2**2+543*tanFi2**4-tanFi2**6)*dLa**8)/40320.
	
	# H2 = h2 - ondul.	# ondulacijo je potrebno modulirat iz geoidnega modela
						# v povprecju znasa ca. 46 m
	H2 = H	
	
	print 'Ravninske nemodulirane koord. D96/TM:', Em, Nm, H2
	
	# -------------------------------------------------------------------------------------------------
	# Modulacija
	# -------------------------------------------------------------------------------------------------
	East = m02*Em + fE
	North = m02*Nm + fN		
	
	print 'Ravninske modulirane koord. v D96/TM:', East, North, H2
	
	
	# -------------------------------------------------------------------------------------------------
	# Kontrola s SiTra.net
	# -------------------------------------------------------------------------------------------------
	Esitra = 499629.458
	Nsitra = 100485.365
	Hsitra = 100
	
	deltaE = Esitra - East
	deltaN = Nsitra - North
	deltaH = Hsitra - H2
	
	print 'Razlike do SiTra:', deltaE, deltaN, deltaH
		
if __name__ == "__main__":
	main()








