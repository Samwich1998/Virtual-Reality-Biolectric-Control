# General
import os

# Plotting
import seaborn as sns
import matplotlib.pyplot as plt


class globalPlottingProtocols:

    def __init__(self):
        # Setup matplotlib
        self.baseFolderName = "_basePlots/"
        plt.rcdefaults()
        plt.ion()

        # Specify the color order.
        self.lightColors = ["#F17FB1", "#5DCBF2", "#B497C9", "#90D6AD", "#FFC162", "#231F20"]  # Red, Blue, Purple, Green, Orange, grey
        self.darkColors = ["#F3757A", "#489AD4", "#7E71B4", "#50BC84", "#F9A770", "#4A4546"]  # Red, Blue, Purple, Green, Orange, grey
        self.blackColor = "#231F20"

        # Set the saving folder
        self.baseSavingDataFolder = None
        self.saveDataFolder = None
        self.datasetName = None

    def setSavingFolder(self, baseSavingDataFolder, stringID, datasetName):
        self.baseSavingDataFolder = baseSavingDataFolder + self.baseFolderName
        self.saveDataFolder = baseSavingDataFolder + stringID
        self.datasetName = datasetName

        if baseSavingDataFolder:
            self._createFolder(self.baseSavingDataFolder)
            if stringID: self._createFolder(self.saveDataFolder)

    @staticmethod
    def _createFolder(filePath):
        if filePath: os.makedirs(os.path.dirname(filePath), exist_ok=True)

    @staticmethod
    def clearFigure(fig=None, legend=None):
        plt.show()  # Ensure the plot is displayed

        # Clear and close the figure/legend if provided
        if legend is not None: legend.remove()
        if fig: fig.clear(); plt.close(fig)

        # Clear all figures and plots
        plt.rcdefaults()  # Reset Matplotlib settings to the defaults.
        plt.close('all')  # Close all open figures

    def displayFigure(self, saveFigureLocation, saveFigureName, baseSaveFigureName=None):
        self._createFolder(self.saveDataFolder + saveFigureLocation)
        plt.savefig(self.saveDataFolder + saveFigureLocation + saveFigureName)
        if baseSaveFigureName is not None: plt.savefig(self.baseSavingDataFolder + f"{self.datasetName} {baseSaveFigureName}")

    def heatmap(self, data, saveDataPath=None, title=None, xlabel=None, ylabel=None):
        # Plot the heatmap
        ax = sns.heatmap(data, robust=True, cmap='icefire')
        # Save the Figure
        sns.set(rc={'figure.figsize': (7, 9)})
        if title: ax.set_title(title)
        if xlabel: plt.xlabel(xlabel)
        if ylabel: plt.ylabel(ylabel)
        fig = ax.get_figure()
        if self.saveDataFolder and saveDataPath:
            fig.savefig(f"{saveDataPath}.pdf", dpi=500, bbox_inches='tight')
            fig.savefig(f"{saveDataPath}.png", dpi=500, bbox_inches='tight')
        self.clearFigure(fig, legend=None)
        plt.rcdefaults()
