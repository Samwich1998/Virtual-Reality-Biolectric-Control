from torch import nn

from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.optimizerMethods import activationFunctions
from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.submodels.modelComponents.neuralOperators.neuralOperatorInterface import neuralOperatorInterface


class specificEmotionModel(neuralOperatorInterface):

    def __init__(self, operatorType, encodedDimension, fourierDimension, numEmotions, numLiftingLayers, numModelLayers, goldenRatio, activationMethod, learningProtocol, neuralOperatorParameters):
        super(specificEmotionModel, self).__init__(sequenceLength=fourierDimension, numInputSignals=numEmotions*numLiftingLayers, numOutputSignals=numEmotions, learningProtocol=learningProtocol, addBiasTerm=False)
        # General model parameters.
        self.activationFunction = activationFunctions.getActivationMethod(activationMethod=activationMethod)
        self.neuralOperatorParameters = neuralOperatorParameters  # The parameters for the neural operator.
        self.learningProtocol = learningProtocol  # The learning protocol for the model.
        self.encodedDimension = encodedDimension  # The dimension of the encoded signal.
        self.fourierDimension = fourierDimension  # The dimension of the fourier signal.
        self.numLiftingLayers = numLiftingLayers  # The number of lifting layers to use.
        self.numModelLayers = numModelLayers  # The number of model layers to use.
        self.operatorType = operatorType  # The operator type for the neural operator.
        self.goldenRatio = goldenRatio  # The golden ratio for the model.
        self.numEmotions = numEmotions  # The number of signals to encode.

        # The neural layers for the signal encoder.
        self.processingLayers, self.neuralLayers, self.addingFlags = nn.ModuleList(), nn.ModuleList(), []
        for layerInd in range(1 + self.numModelLayers // self.goldenRatio): self.addLayer()
        
        # Assert the validity of the input parameters.
        assert self.numModelLayers % self.goldenRatio == 0, "The number of model layers must be divisible by the golden ratio."
        assert self.encodedDimension % 2 == 0, "The encoded dimension must be divisible by 2."
        assert 0 < self.encodedDimension, "The encoded dimension must be greater than 0."

        # Initialize loss holders.
        self.trainingLosses_emotionPrediction = None
        self.testingLosses_emotionPrediction = None
        self.trainingLosses_activityPrediction = None
        self.testingLosses_activityPrediction = None
        self.resetModel()

    def forward(self):
        raise "You cannot call the dataset-specific signal encoder module."

    def resetModel(self):
        # Emotion loss holders.
        self.trainingLosses_emotionPrediction = []  # List of list of prediction training losses. Dim: numEpochs
        self.testingLosses_emotionPrediction = []  # List of list of prediction testing losses. Dim: numEpochs

        # Activity loss holders.
        self.trainingLosses_activityPrediction = []  # List of list of prediction testing losses. Dim: numEpochs
        self.testingLosses_activityPrediction = []  # List of list of prediction testing losses. Dim: numEpochs

    def addLayer(self):
        # Create the layers.
        self.addingFlags.append(not self.addingFlags[-1] if len(self.addingFlags) != 0 else True)
        self.neuralLayers.append(self.getNeuralOperatorLayer(neuralOperatorParameters=self.neuralOperatorParameters, reversibleFlag=False))
        if self.learningProtocol == 'rCNN': self.processingLayers.append(self.postProcessingLayerCNN(numSignals=self.numEmotions * self.numLiftingLayers))
        elif self.learningProtocol == 'rFC': self.processingLayers.append(self.postProcessingLayerFC(sequenceLength=self.fourierDimension))
        else: raise "The learning protocol is not yet implemented."

    def learningInterface(self, layerInd, signalData):
        # Apply the neural operator layer with activation.
        signalData = self.neuralLayers[layerInd](signalData)
        signalData = self.activationFunction(signalData, addingFlag=self.addingFlags[layerInd])

        # Apply the post-processing layer.
        signalData = self.processingLayers[layerInd](signalData)

        return signalData
