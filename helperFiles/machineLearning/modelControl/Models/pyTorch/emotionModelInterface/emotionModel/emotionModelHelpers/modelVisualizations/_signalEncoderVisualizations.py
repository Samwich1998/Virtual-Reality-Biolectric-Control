# General
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from shap.plots.colors._colors import lch2rgb

# Visualization protocols
from helperFiles.globalPlottingProtocols import globalPlottingProtocols
from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.emotionDataInterface import emotionDataInterface
from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.modelConstants import modelConstants


class signalEncoderVisualizations(globalPlottingProtocols):

    def __init__(self, baseSavingFolder, stringID, datasetName):
        super(signalEncoderVisualizations, self).__init__()
        self.setSavingFolder(baseSavingFolder, stringID, datasetName)

    # --------------------- Visualize Model Parameters --------------------- #

    def plotProfilePath(self, relativeTimes, healthProfile, retrainingProfilePath, epoch, saveFigureLocation="signalEncoding/", plotTitle="Health Profile State Path"):
        # Extract the signal dimensions.
        numProfileSteps, batchInd = len(retrainingProfilePath), 0
        noTimes = relativeTimes is None

        if noTimes: relativeTimes = np.arange(start=0, stop=len(healthProfile[batchInd]), step=1)
        for profileStep in range(numProfileSteps): plt.plot(relativeTimes, retrainingProfilePath[profileStep, batchInd], 'o--' if noTimes else '-', c=self.lightColors[1], linewidth=0.25 if noTimes else 1, markersize=4, alpha=0.3*(numProfileSteps - profileStep)/numProfileSteps)
        for profileStep in range(numProfileSteps): plt.plot(relativeTimes, retrainingProfilePath[profileStep, batchInd], 'o--' if noTimes else '-', c=self.lightColors[0], linewidth=0.25 if noTimes else 1, markersize=4, alpha=0.6*(1 - (numProfileSteps - profileStep)/numProfileSteps))
        plt.plot(relativeTimes, healthProfile[batchInd], 'o-' if noTimes else '-', c=self.blackColor, label=f"Health profile", linewidth=1 if noTimes else 2, markersize=5, alpha=0.6 if noTimes else 0.25)
        plt.hlines(y=0, xmin=plt.xlim()[0], xmax=plt.xlim()[1], colors='k', linestyles='dashed', linewidth=1)

        # Plotting aesthetics.
        plt.xlabel("Time (Seconds)")
        plt.title(f"{plotTitle} epoch{epoch}")
        plt.ylabel("Signal (AU)")
        if not noTimes: plt.ylim((-1.5, 1.5))
        else: plt.ylim((-1.5, 1.5))

        # Save the figure.
        if self.saveDataFolder: self.displayFigure(saveFigureLocation=saveFigureLocation, saveFigureName=f"{plotTitle} epochs{epoch}.pdf", baseSaveFigureName=f"{plotTitle}.pdf")
        else: self.clearFigure(fig=None, legend=None, showPlot=True)

    def plotPhysiologicalError(self, relativeTimes, healthProfile, reconstructedPhysiologicalProfile, epoch=0, saveFigureLocation="", plotTitle="Signal Encoding"):
        # Extract the signal dimensions.
        healthError = (healthProfile[:, None, :] - reconstructedPhysiologicalProfile)
        batchSize, numSignals, sequenceLength = reconstructedPhysiologicalProfile.shape
        batchInd = 0

        plt.plot(relativeTimes, healthError[batchInd].mean(axis=0), c=self.blackColor, label=f"Health profile error", linewidth=2, alpha=0.8)
        for signalInd in range(numSignals): plt.plot(relativeTimes, healthError[batchInd, signalInd], c=self.lightColors[0], linewidth=1, alpha=0.1)

        # Plotting aesthetics.
        plt.xlabel("Time (Seconds)")
        plt.title(f"{plotTitle} epoch{epoch}")
        plt.ylabel("Signal error (AU)")

        # Save the figure.
        if self.saveDataFolder: self.displayFigure(saveFigureLocation=saveFigureLocation, saveFigureName=f"{plotTitle} epochs{epoch}.pdf", baseSaveFigureName=f"{plotTitle}.pdf")
        else: self.clearFigure(fig=None, legend=None, showPlot=True)

    def plotPhysiologicalReconstruction(self, relativeTimes, healthProfile, reconstructedPhysiologicalProfile, epoch=0, saveFigureLocation="", plotTitle="Signal Encoding"):
        # Extract the signal dimensions.
        batchSize, numSignals, sequenceLength = reconstructedPhysiologicalProfile.shape
        batchInd = 0

        # Plot the signal reconstruction.
        plt.plot(relativeTimes, healthProfile[batchInd], c=self.blackColor, label=f"Health profile", linewidth=2, alpha=0.8)
        for signalInd in range(numSignals): plt.plot(relativeTimes, reconstructedPhysiologicalProfile[batchInd, signalInd], c=self.lightColors[1], linewidth=1, alpha=0.1)

        # Plotting aesthetics.
        plt.xlabel("Time (Seconds)")
        plt.title(f"{plotTitle} epoch{epoch}")
        plt.ylabel("Signal (AU)")
        plt.ylim((-1.5, 1.5))

        # Save the figure.
        if self.saveDataFolder: self.displayFigure(saveFigureLocation=saveFigureLocation, saveFigureName=f"{plotTitle} epochs{epoch}.pdf", baseSaveFigureName=f"{plotTitle}.pdf")
        else: self.clearFigure(fig=None, legend=None, showPlot=True)

    def plotPhysiologicalOG(self, embeddedProfile, epoch, saveFigureLocation, plotTitle):
        batchInd = 0

        # Plot the signal reconstruction.
        plt.plot(embeddedProfile[batchInd], 'o', c=self.blackColor, label=f"Health profile", linewidth=1, alpha=0.8)

        # Plotting aesthetics.
        plt.xlabel("Time (Seconds)")
        plt.title(f"{plotTitle} epoch{epoch}")
        plt.ylabel("Signal (AU)")
        plt.ylim((-0.75, 0.75))

        # Save the figure.
        if self.saveDataFolder: self.displayFigure(saveFigureLocation=saveFigureLocation, saveFigureName=f"{plotTitle} epochs{epoch}.pdf", baseSaveFigureName=f"{plotTitle}.pdf")
        else: self.clearFigure(fig=None, legend=None, showPlot=True)

    def plotEncoder(self, initialSignalData, reconstructedSignals, comparisonTimes, comparisonSignal, epoch, saveFigureLocation="", plotTitle="Encoder Prediction", numSignalPlots=1):
        # Assert the integrity of the incoming data
        assert initialSignalData.shape[0:2] == comparisonSignal.shape[0:2], f"{initialSignalData.shape} {comparisonSignal.shape}"
        batchSize, numSignals, numEncodedPoints = comparisonSignal.shape
        if batchSize == 0: return None

        # Get the signals to plot.
        plottingSignals = np.arange(0, numSignalPlots)
        plottingSignals = np.concatenate((plottingSignals, np.sort(numSignals - plottingSignals - 1)))
        assert plottingSignals[-1] == numSignals - 1, f"{plottingSignals} {numSignals}"

        # Unpack the data
        datapoints = emotionDataInterface.getChannelData(initialSignalData, channelName=modelConstants.signalChannel)
        timepoints = emotionDataInterface.getChannelData(initialSignalData, channelName=modelConstants.timeChannel)

        batchInd = 0
        for signalInd in plottingSignals:
            # Plot the signal reconstruction.
            plt.plot(timepoints[batchInd, signalInd, :], datapoints[batchInd, signalInd, :], 'o', color=self.blackColor, markersize=2, alpha=0.75, label="Initial Signal")
            plt.plot(timepoints[batchInd, signalInd, :], reconstructedSignals[batchInd, signalInd, :], 'o', color=self.lightColors[0], markersize=2, alpha=1, label="Reconstructed Signal")
            plt.plot(comparisonTimes, comparisonSignal[batchInd, signalInd, :], self.lightColors[1], linewidth=2, alpha=1, label="Resampled Signal")

            # Plotting aesthetics.
            plt.title(f"{plotTitle} epoch{epoch} signal{signalInd + 1}")
            plt.ylabel("Signal (AU)")
            plt.legend(loc="best")
            plt.xlabel("Points")
            plt.ylim((-1.5, 1.5))

            # Save the figure.
            if self.saveDataFolder: self.displayFigure(saveFigureLocation=saveFigureLocation, saveFigureName=f"{plotTitle} epochs{epoch} signalInd{signalInd}.pdf", baseSaveFigureName=f"{plotTitle}.pdf")
            else: self.clearFigure(fig=None, legend=None, showPlot=True)

    def plotSignalEncodingStatePath(self, relativeTimes, compiledSignalEncoderLayerStates, epoch, saveFigureLocation, plotTitle):
        numLayers, numExperiments, numSignals, encodedDimension = compiledSignalEncoderLayerStates.shape
        batchInd, signalInd = 0, 0

        # Interpolate the states.
        compiledSignalEncoderLayerStates = compiledSignalEncoderLayerStates[:, batchInd, signalInd, :]
        numSpecificEncoderLayers = modelConstants.userInputParams['numSpecificEncoderLayers']
        interpolated_states = compiledSignalEncoderLayerStates

        # Create custom colormap (as in your original code)
        blue_lch = [54., 70., 4.6588]
        red_lch = [54., 90., 0.35470565 + 2 * np.pi]
        blue_rgb = lch2rgb(blue_lch)
        red_rgb = lch2rgb(red_lch)
        white_rgb = np.array([1., 1., 1.])

        colors = []
        for alpha in np.linspace(1, 0, 100):
            c = blue_rgb * alpha + (1 - alpha) * white_rgb
            colors.append(c)
        for alpha in np.linspace(0, 1, 100):
            c = red_rgb * alpha + (1 - alpha) * white_rgb
            colors.append(c)
        custom_cmap = LinearSegmentedColormap.from_list("red_transparent_blue", colors)

        # These should be chosen based on your data and how you want to "zoom"
        relativeTimesExtentInterp = (relativeTimes.min(), relativeTimes.max(), 1 + numSpecificEncoderLayers, numLayers - numSpecificEncoderLayers)
        relativeTimesExtent = (relativeTimes.min(), relativeTimes.max(), 0, numLayers)
        plt.figure(figsize=(12, 8))

        # Plot the last layer with its own normalization and colorbar

        # Plot the rest of the layers with the same normalization.
        im0 = plt.imshow(interpolated_states, cmap=custom_cmap, interpolation=None, extent=relativeTimesExtent, aspect='auto', origin='lower', vmin=-1.1, vmax=1.1)
        plt.imshow(interpolated_states[1 + numSpecificEncoderLayers:numLayers - numSpecificEncoderLayers + 1], cmap=custom_cmap, interpolation='bilinear', extent=relativeTimesExtentInterp, aspect='auto', origin='lower', vmin=-1.1, vmax=1.1)
        plt.colorbar(im0, fraction=0.046, pad=0.04)

        # # Plot the last layer with its own normalization and colorbar
        # plt.imshow(interpolated_states[2:-1], cmap=custom_cmap, interpolation=None, extent=relativeTimes, aspect='auto', origin='lower', vmin=first_layer_vmin, vmax=first_layer_vmax)
        # im0 = plt.imshow(interpolated_states[-1:], cmap=custom_cmap, interpolation=None, extent=relativeTimes_finalExtent, aspect='auto', origin='lower', vmin=first_layer_vmin, vmax=first_layer_vmax)
        # plt.colorbar(im0, fraction=0.046, pad=0.04)
        #
        # # Plot the rest of the layers with the same normalization.
        # plt.imshow(interpolated_states[0:1], cmap=custom_cmap, interpolation=None, extent=relativeTimes_initExtent1, aspect='auto', origin='lower', vmin=first_layer_vmin, vmax=first_layer_vmax)
        # plt.imshow(interpolated_states[1:2], cmap=custom_cmap, interpolation=None, extent=relativeTimes_initExtent2, aspect='auto', origin='lower', vmin=first_layer_vmin, vmax=first_layer_vmax)

        # Add horizontal lines to mark layer boundaries
        plt.hlines(y=numLayers - numSpecificEncoderLayers, xmin=plt.xlim()[0], xmax=plt.xlim()[1], colors=self.blackColor, linestyles='dashed', linewidth=2)
        plt.hlines(y=1 + numSpecificEncoderLayers, xmin=plt.xlim()[0], xmax=plt.xlim()[1], colors=self.blackColor, linestyles='dashed', linewidth=2)
        plt.hlines(y=1, xmin=plt.xlim()[0], xmax=plt.xlim()[1], colors=self.blackColor, linestyles='-', linewidth=2)

        # Ticks, labels, and formatting
        yticks = np.array([0, 1, 1] + list(range(2, numLayers - 2)) + [1])
        plt.yticks(ticks=np.arange(start=0.5, stop=numLayers, step=1), labels=yticks, fontsize=12)
        plt.title(label=f"{plotTitle} epoch{epoch}", fontsize=16)
        plt.ylabel(ylabel="Layer Index", fontsize=14)
        plt.xlabel(xlabel="Time", fontsize=14)
        plt.xticks(fontsize=12)
        plt.grid(False)

        # Save or clear figure
        if self.saveDataFolder: self.displayFigure(saveFigureLocation=saveFigureLocation, saveFigureName=f"{plotTitle} epochs{epoch} signalInd{signalInd}.pdf", baseSaveFigureName=f"{plotTitle}.pdf", showPlot=True)
        else: self.clearFigure(fig=None, legend=None, showPlot=False)

    # --------------------- Visualize Model Training --------------------- #

    def plotSignalComparison(self, originalSignal, comparisonSignal, epoch, saveFigureLocation, plotTitle, numSignalPlots=1):
        """ originalSignal dimension: batchSize, numSignals, numTotalPoints """
        # Assert the integrity of the incoming data
        assert originalSignal.shape[0:2] == comparisonSignal.shape[0:2], f"{originalSignal.shape} {comparisonSignal.shape}"

        # Extract the shapes of the data
        batchSize, numSignals, numTotalPoints = originalSignal.shape
        batchSize, numSignals, numEncodedPoints = comparisonSignal.shape
        if batchSize == 0: return None

        batchInd = 0
        # For each signal
        for signalInd in range(numSignals):
            # Plot both the signals alongside each other.
            plt.plot(originalSignal[batchInd, signalInd], 'k', marker='o', linewidth=2)
            plt.plot(np.linspace(0, numTotalPoints, numEncodedPoints), comparisonSignal[batchInd, signalInd], 'tab:red', marker='o', linewidth=1)

            # Format the plotting
            plt.ylabel("Arbitrary Axis (AU)")
            plt.xlabel("Points")
            plt.title(f"{plotTitle} epoch{epoch} signal{signalInd + 1}")
            plt.ylim((-1.5, 1.5))

            # Save the plot
            if self.saveDataFolder: self.displayFigure(saveFigureLocation, saveFigureName=f"{plotTitle} epochs{epoch} signalInd{signalInd}.pdf", baseSaveFigureName=f"{plotTitle}.pdf")
            else: self.clearFigure(fig=None, legend=None, showPlot=True)
            if signalInd + 1 == numSignalPlots: break

    def plotAllSignalComparisons(self, distortedSignals, reconstructedDistortedSignals, trueSignal, epoch, signalInd, saveFigureLocation, plotTitle):
        numSignals, numTotalPoints = reconstructedDistortedSignals.shape
        alphas = np.linspace(0.1, 1, numSignals)

        # Plot all signals in 'distortedSignals'
        for i in range(numSignals):
            plt.plot(distortedSignals[i], '-', color='k', alpha=alphas[i], linewidth=1, markersize=2, zorder=0)
            plt.plot(trueSignal, 'o', color='tab:blue', linewidth=1, markersize=2, zorder=10)
            plt.plot(reconstructedDistortedSignals[i], '-', color='tab:red', linewidth=1, markersize=2, alpha=alphas[i], zorder=5)
        
        # Format the plotting
        plt.title(f"{plotTitle} epoch{epoch} signal{signalInd + 1}")
        plt.xlabel('Time (Seconds)')
        plt.ylabel("Arbitrary Axis (AU)")
        plt.legend(['Noisy Signal', 'True Signal', 'Reconstructed Signal'], loc='best')

        # Save the plot
        if self.saveDataFolder: self.displayFigure(saveFigureLocation=saveFigureLocation, saveFigureName=f"{plotTitle} epochs{epoch} signalInd{signalInd}.pdf", baseSaveFigureName=f"{plotTitle}.pdf")
        else: self.clearFigure(fig=None, legend=None, showPlot=True)

    def plotEigenValueLocations(self, trainingEigenValues, testingEigenValues, epoch, signalInd, saveFigureLocation, plotTitle):
        plt.figure(figsize=(5, 5))
        plt.scatter(trainingEigenValues[signalInd].real.detach().cpu().numpy(), trainingEigenValues[signalInd].imag.detach().cpu().numpy(), color=self.lightColors[1], alpha=0.75)
        plt.scatter(testingEigenValues[signalInd].real.detach().cpu().numpy(), testingEigenValues[signalInd].imag.detach().cpu().numpy(), color=self.lightColors[0], alpha=0.75)
        plt.axhline(0, color='black', linewidth=0.5)
        plt.axvline(0, color='black', linewidth=0.5)

        # Draw the unit circle for reference
        circle = plt.Circle((0, 0), 1.0, color='gray', fill=False, linestyle='--')
        plt.title("Complex Eigenvalues from Layer {}")
        plt.gca().add_patch(circle)
        plt.xlabel("Real part")
        plt.ylabel("Imag part")
        plt.axis('equal')  # make x and y scales the same

        # Save the plot
        if self.saveDataFolder: self.displayFigure(saveFigureLocation=saveFigureLocation, saveFigureName=f"{plotTitle} epochs{epoch} signalInd{signalInd}.pdf", baseSaveFigureName=f"{plotTitle}.pdf")
        else: self.clearFigure(fig=None, legend=None, showPlot=True)

    def plotEigenvalueAngles(self, trainingEigenValues, testingEigenValues, epoch, signalInd, saveFigureLocation, plotTitle):
        trainingAngles, testingAngles = trainingEigenValues.angle().detach().cpu().numpy(), testingEigenValues.angle().detach().cpu().numpy()

        plt.hist(trainingAngles, bins=20, color=self.lightColors[1], alpha=0.75)
        plt.hist(testingAngles, bins=20, color=self.lightColors[0], alpha=0.75)
        plt.title("Distribution of Eigenvalue Angles")
        plt.xlabel("Angle (radians)")
        plt.ylabel("Count")

        # Save the plot
        if self.saveDataFolder: self.displayFigure(saveFigureLocation=saveFigureLocation, saveFigureName=f"{plotTitle} epochs{epoch} signalInd{signalInd}.pdf", baseSaveFigureName=f"{plotTitle}.pdf")
        else: self.clearFigure(fig=None, legend=None, showPlot=True)
