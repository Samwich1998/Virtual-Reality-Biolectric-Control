import os

import numpy as np
import scipy
import torch
import torch.fft
import torch.nn as nn
from matplotlib import pyplot as plt

from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.optimizerMethods import activationFunctions
from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.submodels.modelComponents.reversibleComponents.reversibleInterface import reversibleInterface


class reversibleConvolutionLayer(reversibleInterface):

    def __init__(self, numSignals, sequenceLength, numLayers, activationMethod):
        super(reversibleConvolutionLayer, self).__init__()
        # General parameters.
        self.numFreeParameters = sequenceLength * (sequenceLength - 1) / 2  # The number of free parameters in the model.
        self.numEigenvalues = sequenceLength // 2 + sequenceLength % 2  # The number of parameters in the model.
        self.activationMethod = activationMethod  # The activation method to use.
        self.sequenceLength = sequenceLength  # The length of the input signal.
        self.numSignals = numSignals  # The number of signals in the input data.
        self.numLayers = numLayers  # The number of layers in the reversible linear layer.

        # The indices for the neural weights.
        indices = np.arange(0, self.numEigenvalues, 1)
        self.rowInds, self.colInds = 2*indices, 2*indices + 1

        # Initialize the neural layers.
        self.activationFunction = activationFunctions.getActivationMethod(activationMethod)
        self.jacobianParameter = self.initializeJacobianParams(numSignals)
        self.omegaAngleParams = nn.ParameterList()

        # Create the neural layers.
        for layerInd in range(self.numLayers):
            # Create the neural weights.
            parameters = nn.Parameter(torch.randn(self.numSignals, self.numEigenvalues))
            parameters = nn.init.kaiming_uniform_(parameters)  # kaiming_uniform_
            self.omegaAngleParams.append(parameters)

    def forward(self, inputData):
        for layerInd in range(self.numLayers):
            if not self.forwardDirection: layerInd = self.numLayers - layerInd - 1

            # Apply the weights to the input data.
            if self.activationMethod == 'none': inputData = self.applyLayer(inputData, layerInd)
            else: inputData = self.activationFunction(inputData, lambda X: self.applyLayer(X, layerInd), forwardFirst=False)

        return inputData

    def applyLayer(self, inputData, layerInd):
        # Assert the validity of the input parameters.
        batchSize, numSignals, sequenceLength = inputData.size()
        assert sequenceLength == self.sequenceLength, f"The sequence length is not correct: {sequenceLength}, {self.sequenceLength}"
        assert numSignals == self.numSignals, f"The number of signals is not correct: {numSignals}, {self.numSignals}"

        # Apply the neural weights to the input data.
        neuralWeights = self.getExpA(layerInd, inputData.device)  # = exp(A)
        outputData = torch.einsum('bns,nsi->bni', inputData, neuralWeights)  # -> exp(A) @ f(x)
        outputData = self.applyManifoldScale(outputData, self.jacobianParameter)  # TODO
        # The inverse would be f-1(exp(-A) @ [exp(A) @ f(x)]) = X

        return outputData

    # ------------------- Linearity ------------------- #

    def getExpA(self, layerInd, device):
        A = self.getA(layerInd, device)  # Get the linear operator in the exponent.
        if self.forwardDirection: A = -A  # Ensure the neural weights are symmetric.

        # Get the exponential of the linear operator.
        neuralWeights = A.matrix_exp()  # For orthogonal matrices: A.exp().inverse() = (-A).exp(); If A is Skewed Symmetric: A.exp().inverse() = A.exp().transpose()
        return neuralWeights  # exp(A)

    def getA(self, layerInd, device):
        # Get the rotations.
        A = torch.zeros(self.numSignals, self.sequenceLength, self.sequenceLength, device=device)
        omegaAngles = self.getSubdomainRotations(layerInd, device)
        # omegaAngles: numSignals, numEigenvalues

        # Gather the corresponding kernel values for each position for a skewed symmetric matrix.
        A[:, self.rowInds, self.colInds] = -omegaAngles[layerInd]
        A[:, self.colInds, self.rowInds] = omegaAngles[layerInd]
        # In Jordan 2x2 Blocks, A: numSignals, sequenceLength, sequenceLength

        return A

    # ------------------- Activation Functions ------------------- #

    def applyManifoldScale(self, inputData, jacobianParameter):
        scalarValues = self.getJacobianScalar(jacobianParameter).expand_as(inputData)
        if not reversibleInterface.forwardDirection: return inputData * scalarValues
        else: return inputData / scalarValues

    @staticmethod
    def initializeJacobianParams(numSignals):
        return nn.Parameter(torch.zeros((1, numSignals, 1)))

    @staticmethod
    def getJacobianScalar(jacobianParameter):
        jacobianMatrix = 0.95 + 0.1 * torch.sigmoid(jacobianParameter)
        return jacobianMatrix

    # ------------------- Activation Functions ------------------- #

    def getSubdomainRotations(self, layerInd, device):
        # Scale the values to an angle.
        omegaAngles = torch.tanh(self.omegaAngleParams[layerInd])  # Scale between [-1, 1]
        omegaAngles = torch.pi*omegaAngles  # Scale between [-pi, pi]
        return omegaAngles.to(device)

    def getReversibleActivationCurves(self):
        return self.activationFunction.getActivationCurve(x_min=-2, x_max=2, num_points=200)

    def getReversibleActivationParams(self):
        params = self.activationFunction.getActivationParams()
        params = [param.detach().cpu().numpy() for param in params]
        return params

    def printParams(self):
        # Count the trainable parameters.
        numParams = sum(_p.numel() for _p in self.parameters() if _p.requires_grad) / self.numSignals
        print(f'The model has {numParams} trainable parameters.')


if __name__ == "__main__":
    # for i in [2, 4, 8, 16, 32, 64, 128, 256]:
    # for i in [16, 32, 64, 128, 256]:
    reconstructionFlag = True

    try:
        # for layers, sequenceLength2 in [(2, 256), (2, 128), (2, 64), (2, 32), (2, 16), (2, 8), (2, 4), (2, 2)]:
        for _layerInd, sequenceLength2 in [(1, 128)]:
            # General parameters.
            _batchSize, _numSignals, _sequenceLength = 256, 256, sequenceLength2
            _kernelSize = 2*_sequenceLength - 1
            _activationMethod = 'reversibleLinearSoftSign'  # reversibleLinearSoftSign
            _numLayers = _layerInd

            # Set up the parameters.
            neuralLayerClass = reversibleConvolutionLayer(numSignals=_numSignals, sequenceLength=_sequenceLength, numLayers=_numLayers, activationMethod=_activationMethod)
            healthProfile = torch.randn(_batchSize, _numSignals, _sequenceLength)
            healthProfile = healthProfile / 6

            # Perform the convolution in the fourier and spatial domains.
            if reconstructionFlag: _forwardData, _reconstructedData = neuralLayerClass.checkReconstruction(healthProfile, atol=1e-6, numLayers=1, plotResults=True)
            else: _forwardData = neuralLayerClass.forward(healthProfile)
            neuralLayerClass.printParams()

            ratio = (_forwardData.norm(dim=-1) / healthProfile.norm(dim=-1)).view(-1).detach().numpy()
            if abs(ratio.mean() - 1) < 0.1: plt.hist(ratio, bins=150, alpha=0.2, label=f'len{_sequenceLength}_layers={_layerInd}', density=True)
            print(ratio.mean())

            # Plot the Gaussian fit
            xmin, xmax = plt.xlim()
            x = np.linspace(xmin, xmax, num=1000)
            mu, std = scipy.stats.norm.fit(ratio)
            p = scipy.stats.norm.pdf(x, mu, std)
            plt.plot(x, p, 'k', linewidth=2, label=f'Gaussian fit: mu={mu:.8f}$, sigma={std:.8f}$')

            # Figure settings.
            plt.title(f'Fin', fontsize=14)  # Increase title font size for readability
            plt.xlim(0.98, 1.02)
            plt.legend()

            # Save the plot.
            os.makedirs('_lipshitz/', exist_ok=True)
            plt.savefig(f'_lipshitz/len{sequenceLength2}_layers={_numLayers}')
            plt.show()
    except Exception as e: print(f"Error: {e}")
