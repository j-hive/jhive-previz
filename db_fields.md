`ID`: internal ID
`CAT_ID`: DJA ID
`RA`: RA
`DEC`: DEC
`z_spec`: spectroscopic redshift from main phot_corr catalog
`z_phot`: photometric redshift from ez catalog
`logM_50`: median log current stellar mass in solar masses
`logSFRinst_50`: median log of instantaneous star formation rate 
`logZsol_50`: median log metallicity with respect to solar 
`Av_50`: V-band extinction in magnitudes 
`zfit_50`: the fitted redshift, usually ~ z_phot
`logMt_50`: median log total formed stellar mass in solar masses
`logSFRtuple_50`: median log SFR (internal parameter, mostly equivalent to SFRinst)
`logSFR10_50`: median log SFR over last 10 Myr
`logSFR100_50`: median log SFR over last 100 Myr
`logSFR300_50`: median log SFR over last 300 Myr
`logSFR1000_50`: median log SFR over last 1000 Myr
`t25_50`: median fraction of the age of the universe that galaxy formed 25% of its mass
`t50_50`: median fraction of the age of the universe that galaxy formed 50% of its mass
`t75_50`: median fraction of the age of the universe that galaxy formed 75% of its mass
`nparam`: number of tx parameters 
`nbands`: number of good photometric bands used for the fit
`chi2`: the fit likelihood
`fit_flags`: flags for galaxies that: have nan values for mass, have SFR uncertainties > cutoff, are flagged as a star, or have extremely large chi2