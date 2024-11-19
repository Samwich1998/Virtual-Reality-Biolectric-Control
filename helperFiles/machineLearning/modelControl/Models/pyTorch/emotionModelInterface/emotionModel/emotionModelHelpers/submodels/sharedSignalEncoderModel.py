import torch
from torch import nn

from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.generalMethods.generalMethods import generalMethods
from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.modelConstants import modelConstants
from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.modelParameters import modelParameters
from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.optimizerMethods import activationFunctions
from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.submodels.modelComponents.neuralOperators.neuralOperatorInterface import neuralOperatorInterface
from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.submodels.modelComponents.reversibleComponents.reversibleInterface import reversibleInterface


class sharedSignalEncoderModel(neuralOperatorInterface):

    def __init__(self, operatorType, encodedDimension, numLiftingLayers, goldenRatio, learningProtocol, neuralOperatorParameters):
        super(sharedSignalEncoderModel, self).__init__(operatorType=operatorType, sequenceLength=encodedDimension, numInputSignals=numLiftingLayers, numOutputSignals=numLiftingLayers, addBiasTerm=False)
        # General model parameters.
        self.neuralOperatorParameters = neuralOperatorParameters  # The parameters for the neural operator.
        self.encodedTimeWindow = modelConstants.timeWindows[-1]  # The time window for the encoded signal.
        self.activationMethod = self.getActivationType()  # The activation method to use.
        self.fourierDimension = encodedDimension // 2 + 1  # The dimension of the fourier data.
        self.learningProtocol = learningProtocol  # The learning protocol for the model.
        self.encodedDimension = encodedDimension  # The dimension of the encoded signal.
        self.numLiftingLayers = numLiftingLayers  # The number of lifting layers to use.
        self.goldenRatio = goldenRatio  # The golden ratio for the model.

        # Initialize the pseudo-encoded times for the fourier data.
        pseudoEncodedTimes = torch.linspace(start=0, end=self.encodedTimeWindow, steps=self.encodedDimension).flip(dims=[0])
        self.register_buffer(name='pseudoEncodedTimes', tensor=pseudoEncodedTimes)  # Non-learnable parameter.
        deltaTimes = torch.unique(self.pseudoEncodedTimes.diff().round(decimals=4))
        assert len(deltaTimes) == 1, f"The time gaps are not similar: {deltaTimes}"

        # The neural layers for the signal encoder.
        self.activationFunction = activationFunctions.getActivationMethod(self.activationMethod)
        self.processingLayers, self.neuralLayers = nn.ModuleList(), nn.ModuleList()

    def forward(self):
        raise "You cannot call the dataset-specific signal encoder module."

    def addLayer(self):
        self.neuralLayers.append(self.getNeuralOperatorLayer(neuralOperatorParameters=self.neuralOperatorParameters, reversibleFlag=True))
        if self.learningProtocol == 'rCNN': self.processingLayers.append(self.postProcessingLayerRCNN(numSignals=self.numLiftingLayers, sequenceLength=self.encodedDimension, activationMethod=self.activationMethod))
        elif self.learningProtocol == 'rFC': self.processingLayers.append(self.postProcessingLayerRFC(numSignals=self.numLiftingLayers, sequenceLength=self.encodedDimension, activationMethod=self.activationMethod))
        else: raise "The learning protocol is not yet implemented."

    def learningInterface(self, layerInd, signalData):
        # Extract the signal data parameters.
        batchSize, numSignals, signalLength = signalData.shape
        numSignals = numSignals // self.numLiftingLayers

        # Reshape the signal data.
        signalData = signalData.view(batchSize*numSignals, self.numLiftingLayers, signalLength)

        # For the forward/harder direction.
        if not reversibleInterface.forwardDirection:
            # Apply the neural operator layer with activation.
            signalData = self.activationFunction(signalData, lambda x: self.neuralLayers[layerInd].reversibleInterface(x))
            signalData = self.processingLayers[layerInd](signalData)
        else:
            # Get the reverse layer index.
            pseudoLayerInd = len(self.neuralLayers) - layerInd - 1
            assert 0 <= pseudoLayerInd < len(self.neuralLayers), f"The pseudo layer index is out of bounds: {pseudoLayerInd}, {len(self.neuralLayers)}, {layerInd}"

            # Apply the neural operator layer with activation.
            signalData = self.processingLayers[pseudoLayerInd](signalData)
            signalData = self.activationFunction(signalData, lambda x: self.neuralLayers[pseudoLayerInd].reversibleInterface(x))

        # Reshape the signal data.
        signalData = signalData.view(batchSize, numSignals*self.numLiftingLayers, signalLength)

        return signalData.contiguous()

    def calculateOptimalLoss(self, initialSignalData, printLoss=True):
        with torch.no_grad():
            # Perform the optimal compression via PCA and embed channel information (for reconstruction).
            pcaProjection, principal_components = generalMethods.svdCompression(initialSignalData, self.numEncodedSignals, standardizeSignals=True)
            # Loss for PCA reconstruction
            pcaReconstruction = torch.matmul(principal_components, pcaProjection)
            pcaReconstruction = (pcaReconstruction + initialSignalData.mean(dim=-1, keepdim=True)) * initialSignalData.std(dim=-1, keepdim=True)
            pcaReconstructionLoss = (initialSignalData - pcaReconstruction).pow(2).mean(dim=2).mean(dim=1)
            if printLoss: print("\tFIRST Optimal Compression Loss STD:", pcaReconstructionLoss.mean().item())

            return pcaReconstructionLoss

    def printParams(self):
        # Count the trainable parameters.
        numParams = sum(p.numel() for p in self.parameters() if p.requires_grad)
        print(f'The model has {numParams} trainable parameters.')


if __name__ == "__main__":
    # General parameters.
    _neuralOperatorParameters = modelParameters.getNeuralParameters({'waveletType': 'bior3.7'})['neuralOperatorParameters']
    _batchSize, _numSignals, _sequenceLength = 2, 128, 300

    # Set up the parameters.
    neuralLayerClass = sharedSignalEncoderModel(operatorType='wavelet', encodedDimension=_sequenceLength, numLiftingLayers=1, goldenRatio=4, learningProtocol='rCNN', neuralOperatorParameters=_neuralOperatorParameters)
    neuralLayerClass.addLayer()

    # Print the number of trainable parameters.
    neuralLayerClass.printParams()
