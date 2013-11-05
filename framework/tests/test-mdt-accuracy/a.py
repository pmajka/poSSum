import numpy as np

mu, sigma, n = 64, 8, 100

samples = np.random.normal(mu, sigma, size=n)

for i in range(n):
    v=samples[i]
    print "convert -size 256x256 xc:black -fill white -stroke none -draw \"rectangle %d,64 192,128\" img_%03d.png; c2d img_%03d.png -o %04d.nii.gz" %(v,i,i,i)
