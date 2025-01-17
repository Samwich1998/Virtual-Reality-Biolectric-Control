from torch import nn

from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.modelConstants import modelConstants
from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.modelParameters import modelParameters
from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.submodels.profileModel import profileModel
from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.submodels.modelComponents.neuralOperators.neuralOperatorInterface import neuralOperatorInterface
from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.submodels.modelComponents.reversibleComponents.reversibleInterface import reversibleInterface


class specificSignalEncoderModel(neuralOperatorInterface):

    def __init__(self, numExperiments, operatorType, encodedDimension, featureNames, numSpecificEncoderLayers, learningProtocol, neuralOperatorParameters):
        super(specificSignalEncoderModel, self).__init__(operatorType=operatorType, sequenceLength=encodedDimension, numInputSignals=len(featureNames), numOutputSignals=len(featureNames), addBiasTerm=False)
        # General model parameters.
        self.neuralOperatorParameters = neuralOperatorParameters  # The parameters for the neural operator.
        self.numSpecificEncoderLayers = numSpecificEncoderLayers  # The number of specific encoder layers.
        self.learningProtocol = learningProtocol  # The learning protocol for the model.
        self.encodedDimension = encodedDimension  # The dimension of the encoded signal.
        self.numExperiments = numExperiments  # The number of experiments.
        self.numSignals = len(featureNames)  # The number of signals to encode.
        self.featureNames = featureNames  # The names of the signals to encode.

        # The neural layers for the signal encoder.
        self.profileModel = profileModel(numExperiments=numExperiments, numSignals=self.numSignals, encodedDimension=encodedDimension)
        self.processingLayers, self.neuralLayers = nn.ModuleList(), nn.ModuleList()
        for _ in range(self.numSpecificEncoderLayers): self.addLayer()

        # Assert the validity of the input parameters.
        assert self.encodedDimension % 2 == 0, "The encoded dimension must be divisible by 2."
        assert 0 < self.encodedDimension, "The encoded dimension must be greater than 0."

        # Initialize loss holders.
        self.trainingLosses_signalReconstruction, self.testingLosses_signalReconstruction = None, None
        self.scalingFactorsPath, self.givensAnglesPath = None, None
        self.givensAnglesFeaturesPath = None
        self.activationParamsPath = None
        self.resetModel()

    def forward(self): raise "You cannot call the dataset-specific signal encoder module."

    def resetModel(self):
        # Signal encoder reconstruction holders.
        self.trainingLosses_signalReconstruction = []  # List of list of data reconstruction training losses. Dim: numEpochs, numTrainingSignals
        self.testingLosses_signalReconstruction = []  # List of list of data reconstruction testing losses. Dim: numEpochs, numTestingSignals
        self.givensAnglesFeaturesPath = []  # List of Givens angles. Dim: numEpochs, numModuleLayers, numParams, numSignals
        self.activationParamsPath = []  # List of activation bounds. Dim: numEpochs, numActivations, numActivationParams
        self.scalingFactorsPath = []  # List of Givens angles. Dim: numEpochs, numModuleLayers, numSignals
        self.givensAnglesPath = []  # List of Givens angles. Dim: numEpochs, numModuleLayers, numParams, numSignals

    def addLayer(self):
        self.neuralLayers.append(self.getNeuralOperatorLayer(neuralOperatorParameters=self.neuralOperatorParameters, reversibleFlag=True))
        if self.learningProtocol == 'rCNN': self.processingLayers.append(self.postProcessingLayerRCNN(numSignals=self.numSignals, sequenceLength=self.encodedDimension))
        elif self.learningProtocol == 'FC': self.processingLayers.append(self.postProcessingLayerFC(sequenceLength=self.encodedDimension))
        elif self.learningProtocol == 'CNN': self.processingLayers.append(self.postProcessingLayerCNN(numSignals=self.numSignals))
        else: raise "The learning protocol is not yet implemented."

    def learningInterface(self, layerInd, signalData):
        # For the forward/harder direction.
        if not reversibleInterface.forwardDirection:
            # Apply the neural operator layer with activation.
            signalData = self.neuralLayers[layerInd](signalData)
            signalData = self.processingLayers[layerInd](signalData)
        else:
            # Get the reverse layer index.
            pseudoLayerInd = len(self.neuralLayers) - layerInd - 1
            assert 0 <= pseudoLayerInd < len(self.neuralLayers), f"The pseudo layer index is out of bounds: {pseudoLayerInd}, {len(self.neuralLayers)}, {layerInd}"

            # Apply the neural operator layer with activation.
            signalData = self.processingLayers[pseudoLayerInd](signalData)
            signalData = self.neuralLayers[pseudoLayerInd](signalData)

        return signalData.contiguous()

    def printParams(self):
        # Count the trainable parameters.
        numProfileParams = sum(p.numel() for name, p in self.named_parameters() if p.requires_grad and 'profileModel' in name) / self.numExperiments
        # numParams = sum(p.numel() for name, p in self.named_parameters() if p.requires_grad and 'profileModel' not in name) / self.numSignals
        numParams = (sum(p.numel() for name, p in self.named_parameters()) - numProfileParams) / self.numSignals

        # Print the number of trainable parameters.
        totalParams = numParams*self.numSignals + numProfileParams*self.numExperiments
        print(f'The model has {totalParams} trainable parameters: {numProfileParams + numParams} split between {numParams} per signal and {numProfileParams} per experiment.')


if __name__ == "__main__":
    # General parameters.
    _neuralOperatorParameters = modelParameters.getNeuralParameters({'waveletType': 'bior3.1'})['neuralOperatorParameters']
    _batchSize, _numSignals, _sequenceLength = 1, 1, 128
    _featureNames = [f"signal_{i}" for i in range(_numSignals)]
    modelConstants.profileDimension = 128
    _numSpecificEncoderLayers = 1
    _numSharedEncoderLayers = 4

    # Set up the parameters.
    modelConstants.initialProfileAmp = 0.001
    modelConstants.userInputParams['numSharedEncoderLayers'] = _numSharedEncoderLayers
    modelConstants.userInputParams['numSpecificEncoderLayers'] = _numSpecificEncoderLayers
    neuralLayerClass = specificSignalEncoderModel(numExperiments=_batchSize, operatorType='wavelet', encodedDimension=_sequenceLength, featureNames=_featureNames, numSpecificEncoderLayers=_numSpecificEncoderLayers, learningProtocol='rCNN', neuralOperatorParameters=_neuralOperatorParameters)
    neuralLayerClass.printParams()
