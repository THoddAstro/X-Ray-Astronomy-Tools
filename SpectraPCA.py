"""
Spectrum and Spectral PCA Classes.
These classes can be used to perform PCA on a set of spectra.
Create a SpectralPCA object with a list of Spectra objects and call `do_pca()` to do the PCA.

Author: Thomas Hodd

Date - 14th May 2026

Version - 1.2
"""
import numpy as np
import astropy.io.fits as pyfits
from matplotlib import pyplot as plt
from matplotlib.ticker import *

COLOURS = ["dodgerblue", "orangered", "forestgreen", "deeppink", "darkturquoise", "orange",
           "darkorchid", "lawngreen", "mediumblue", "violet", "black", "grey", "peru"]


class Spectrum:
    """
    X-ray Spectrum object.

    Parameters
    ==========
    spec_file: str
        Spectrum FITS file (Should be *_src.pha or similar)
    rmf_file: LightCurve
        Spectrum RMF file
    energy_bin_edges: np.ndarray
        Array of energy bin edges to use for binning
    bkg_corr: bool
        Apply background correction, requires corresponding bkg file (*_bkg.pha or similar)
    n_errs: int
        Number of perturbed spectra to use for error estimation

    Attributes
    ==========
    spec_file: str
        Spectrum FITS file name
    rmf_file: LightCurve
        Spectrum RMF file name
    energy_bin_edges: np.ndarray
        Array of energy bin edges to use for binning
    counts: np.ndarray
        Array containing the spectrum counts in each bin
    channels: np.ndarray
        Array containing the channel edges of each bin
    energies: np.ndarray
        Array of energy bin midpoints
    exptime: float
        Spectrum exposure time
    perturbed_spectra: list
        Array of perturbed spectra counts for error estimation
    """

    def __init__(self, spec_file: str, rmf_file: str, energy_bin_edges: np.ndarray, bkg_corr: bool = True, n_errs: int = 20) -> None:
        self.spec_file = spec_file
        self.rmf_file = rmf_file
        self.energy_bin_edges = energy_bin_edges
        self.energies = energy_bin_edges[:-1]  # (self.energy_bin_edges[:-1] + self.energy_bin_edges[1:]) / 2
        self.__n_errs = n_errs

        # Initialise arrays
        self.counts = np.empty(0, dtype=int)
        self.channels = np.empty(0, dtype=int)
        self.perturbed_spectra = []
        self.__fluxes = np.empty(0)
        self.__channel_bins = np.empty(0, dtype=int)

        # Read source spectrum FITS
        src = pyfits.open(spec_file)
        src_data = src['SPECTRUM'].data
        src_hdr = src['SPECTRUM'].header
        self.exptime = src_hdr['EXPOSURE']

        # Read background spectrum FITS
        if bkg_corr:
            bkg_file = self.spec_file.replace("src", "bkg")
            bkg = pyfits.open(bkg_file)
            bkg_data = bkg['SPECTRUM'].data
            bkg_hdr = bkg['SPECTRUM'].header
            src_backscal = src_hdr['BACKSCAL']
            backscal = bkg_hdr['BACKSCAL']
            bkg_exptime = bkg_hdr['EXPOSURE']

        # Extract data from FITS
        for i in range(0, len(src_data)):
            row = src_data[i]
            self.channels = np.append(self.channels, row[0])
            self.__fluxes = np.append(self.__fluxes, row[1])

            # Apply background correction
            if bkg_corr:
                backrow = bkg_data[i]
                counts = row[1] - backrow[1] * (self.exptime / bkg_exptime) * (src_backscal / backscal)
            # Or don't
            else:
                counts = row[1]

            # Add counts (/s) to array
            self.counts = np.append(self.counts, counts / self.exptime)

        # Read RMF
        rmf_file = pyfits.open(self.rmf_file)
        ebounds = rmf_file["EBOUNDS"].data
        emins = np.empty(0, dtype=float)
        emaxs = np.empty(0, dtype=float)
        channels = np.empty(0, dtype=int)

        # Get channels edges for each energy bin
        for row in ebounds:
            channels = np.append(channels, row[0])
            emins = np.append(emins, row[1])
            emaxs = np.append(emaxs, row[2])
        if emaxs[-1] < emaxs[0]:
            channels = np.flipud(np.array(channels))
            emins = np.flipud(np.array(emins))
        for e in self.energy_bin_edges:
            for i in range(1, len(channels) - 1):
                if emins[i] <= e < emins[i + 1]:
                    self.__channel_bins = np.append(self.__channel_bins, channels[i])

        # Apply binning
        binned_counts = np.empty(0)
        for bmin, bmax in zip(self.__channel_bins[:-1], self.__channel_bins[1:]):
            binned_counts = np.append(binned_counts, sum(self.counts[bmin:bmax]) / len(self.counts[bmin:bmax]))
        self.counts = binned_counts

        # Generate random perturbed spectra for PCA error estimation
        for i in range(0, self.__n_errs):
            spec_i = [max([c, 0]) + np.random.randn() * max([c, 0]) ** 0.5 for c in self.__fluxes]
            spec_i = [i / self.exptime for i in spec_i]
            binned_counts = np.empty(0)
            for bmin, bmax in zip(self.__channel_bins[:-1], self.__channel_bins[1:]):
                binned_counts = np.append(binned_counts, sum(spec_i[bmin:bmax]) / len(spec_i[bmin:bmax]))
            self.perturbed_spectra.append(binned_counts)

    def __str__(self):
        return f"Spectrum object of {self.spec_file} | {self.rmf_file}"

    def plot(self, energy: bool = True) -> None:
        """
        Plot the spectrum.

        :param energy: If True, x-axis units are keV, else they are channel
        :return: None
        """
        if energy:
            plt.errorbar(self.energies, self.counts, linewidth=0, elinewidth=1, c="k", markersize=1, marker="+")
            plt.xlabel("Energy (keV)")
        else:
            plt.errorbar(self.channels, self.counts, linewidth=0, elinewidth=1, c="k", markersize=1, marker="+")
            plt.xlabel("Channel")
        plt.tick_params(axis="both", which="both", direction="in", top=True, right=True)

        plt.xscale("log")
        plt.yscale("log")

        plt.ylabel("Counts (/s)")

        plt.show()


class SpectralPCA:
    """
    Class for computing the PCA of a given set of spectra.

    Parameters
    ==========
    spectra: list[Spectrum]
        List of spectra to perform PCA with, must be Spectrum objects

    Attributes
    ==========
    spectra: list[Spectrum]
        List of spectra used in PCA
    channels: np.ndarray
        Array containing the channel edges of each bin
    energies: np.ndarray
        Array of energy bin midpoints
    mean_spectrum: np.ndarray
        Mean spectrum counts array of all spectra
    norm_spectra: np.ndarray
        Array containing the normalised spectrum counts for each spectrum
    principal_comps: np.ndarray
        Array containing the principal components
    eigenvals: np.ndarray
        Array containing eigenvalues for each eigenspectrum
    err_spectra: np.ndarray
        Array containing estimated errors for each eigenspectrum
    err_eigenval: np.ndarray
        Array containing estimated errors on each eigenvalue
    """
    def __init__(self, spectra: list[Spectrum]) -> None:
        self.spectra = spectra
        self.channels = spectra[0].channels
        self.energies = spectra[0].energies
        self._n_errs = len(spectra[0].perturbed_spectra)
        self._n_spectra = len(spectra)
        self.__perturbed_spectra = [s.perturbed_spectra for s in spectra]

        self.mean_spectrum = []
        self.norm_spectra = []

        self.principal_comps = []
        self.eigenvals = []

        self.err_spectra = []
        self.err_eigenval = []

    def __str__(self):
        return f"SpectralPCA with {len(self.spectra)} spectra, {len(self.channels)} channels, {len(self.energies)} energies ({self.energies[0]}-{self.energies[-1]})"

    def __normalise_spectra(self, subtract: bool = True) -> None:
        """
        Normalises the spectra.

        :param subtract: If True the mean will be subtracted from the normalised spectra.
        :return: None
        """
        # Create array of counts
        spectra_counts_array = np.array([s.counts for s in self.spectra])

        # Calculate the mean spectrum
        self.mean_spectrum = np.mean(spectra_counts_array, axis=0)

        # Normalise to mean
        if subtract:
            normalised = (spectra_counts_array - self.mean_spectrum) / self.mean_spectrum
        else:
            normalised = spectra_counts_array / self.mean_spectrum
        self.norm_spectra = np.transpose(normalised)

    def __get_pca_errors(self) -> None:
        """
        Estimates the errors in the PCA using the perturbed spectra.

        :return: None
        """
        # Get perturbed spectra
        random_spectra = [[[(c - m) / m for c, m in zip(spectrum, self.mean_spectrum)] for spectrum in rand_spec]for rand_spec in self.__perturbed_spectra]

        perturbed_pcs = []
        perturbed_eigenvals = []

        # Do PCA on each set
        for i in range(self._n_errs):
            error_array = np.transpose([spec_set[i] for spec_set in random_spectra])
            u, s, _ = np.linalg.svd(error_array)
            u = u.T

            if i == 0:
                u0 = u.copy()

            # Normalise eigenvalues
            eigenvals_sq = s ** 2
            perturbed_eigenvals.append(eigenvals_sq / eigenvals_sq.sum())
            for j in range(len(u)):
                if np.dot(u0[j], u[j]) < 0:
                    u[j] *= -1

            perturbed_pcs.append(u)

        # Calculate errors
        perturbed_eigenvals = np.array(perturbed_eigenvals)
        self.err_eigenval = np.std(perturbed_eigenvals, axis=0)
        self.err_spectra = np.std(np.array(perturbed_pcs), axis=0)

        # Print eigenvalues with uncertainties
        for i in range(0, self._n_spectra - 1):
            print(f"Eigenvector {i + 1}: {str(self.eigenvals[i] * 100)[0:6]} +/- {str(self.eigenvals[i + 1] * 100)[0:6]} %")
        print(f"Remaining: {str(sum(self.eigenvals[self._n_spectra:]) * 100)[0:6]}%")

    def do_pca(self, errors: bool = True) -> None:
        """
        Does the PCA for the spectra.
        Once called `principal_comps` and `eigenvals` will be calculated.

        :param errors: If True errors will be estimated for the PCA
        :return: None
        """
        # Normalise the spectra and subtract the mean
        self.__normalise_spectra()

        # Do PCA (Using singular value decomposition)
        u, s, _ = np.linalg.svd(self.norm_spectra)
        self.principal_comps = np.transpose(u)

        # Get Eigenvalues
        eigenvals = [i ** 2 for i in s]
        self.eigenvals = [i / sum(eigenvals) for i in eigenvals]

        # Get errors
        if errors:
            self.__get_pca_errors()

    def plot_pca_result(self, max_spec: int = 6, flip: bool = False) -> None:
        """
        Plots the results of the PCA.

        :param max_spec: Maximum number of eigenspectra to plot
        :param flip: Switch +ve/-ve to keep PC 1 positive
        :return: None
        """
        # Eigenspectra plot
        n_spec = min(self._n_spectra, max_spec)
        _, ax = plt.subplots(n_spec, 1, sharex=True, gridspec_kw={'hspace': 0}, figsize=(8, n_spec * 2))
        for i in range(0, n_spec):
            rate = -self.principal_comps[i] if flip else self.principal_comps[i]
            ax[i].errorbar(self.energies, rate, self.err_spectra[i], ls='none', c=COLOURS[i % len(COLOURS)])
            ax[i].set_xscale("log")
            ax[i].axhline(y=0, color="grey", linestyle="--", zorder=0)
            ax[i].set_xlim(min(self.energies), max(self.energies))
            ax[i].tick_params(axis="both", which="both", direction="in", top=True, right=True)
        ax[-1].set_xlabel("Energy (KeV)")
        ax[-1].xaxis.set_major_locator(FixedLocator([0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100]))
        ax[-1].xaxis.set_minor_locator(FixedLocator([0.3, 0.4, 0.6, 0.7, 0.8, 0.9, 3, 4, 6, 7, 8, 9, 15, 30, 40, 60, 70, 80, 90]))
        ax[-1].xaxis.set_major_formatter(ScalarFormatter())
        ax[0].set_ylabel("Rate")

        # Fvar plot
        plt.figure(figsize=(6, 4))
        plt.xlabel("Eigenvector")
        plt.ylabel("Fractional Variability")
        for i in range(0, n_spec):
            plt.plot(i + 1, [self.eigenvals[i]], marker='o', ls='-', ms=8, c=COLOURS[i % len(COLOURS)])
        plt.tick_params(axis="both", which="both", direction="in", top=True, right=True)
        plt.yscale("log")

        plt.show()
