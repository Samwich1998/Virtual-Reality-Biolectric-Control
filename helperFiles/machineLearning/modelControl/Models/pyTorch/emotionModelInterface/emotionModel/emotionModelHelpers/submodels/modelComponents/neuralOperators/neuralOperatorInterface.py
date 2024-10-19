from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.submodels.modelComponents.neuralOperators.waveletOperator.waveletNeuralOperatorLayer import waveletNeuralOperatorLayer
from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.submodels.modelComponents.signalEncoderComponents.emotionModelWeights import emotionModelWeights


class neuralOperatorInterface(emotionModelWeights):

    def __init__(self, sequenceLength, numInputSignals, numOutputSignals, learningProtocol, addBiasTerm):
        super().__init__()
        # General parameters.
        self.learningProtocol = learningProtocol  # The learning protocol for the neural operator.
        self.numOutputSignals = numOutputSignals  # The number of output signals.
        self.numInputSignals = numInputSignals  # The number of input signals.
        self.sequenceLength = sequenceLength  # The length of the input signals.
        self.addBiasTerm = addBiasTerm  # Whether to add a bias term to the neural operator.

    def getNeuralOperatorLayer(self, neuralOperatorParameters):
        # Decide on the neural operator layer.
        if self.operatorType == 'wavelet': return self.initializeWaveletLayer(neuralOperatorParameters[self.operatorType])
        else: raise ValueError(f"The operator type ({self.operatorType}) must be in ['wavelet'].")

    def initializeWaveletLayer(self, neuralOperatorParameters):
        # Unpack the neural operator parameters.
        encodeHighFrequencyProtocol = neuralOperatorParameters['encodeHighFrequencyProtocol']  # The protocol for encoding the high frequency signals.
        encodeLowFrequencyProtocol = neuralOperatorParameters['encodeLowFrequencyProtocol']  # The protocol for encoding the low frequency signals.
        skipConnectionProtocol = neuralOperatorParameters['skipConnectionProtocol']  # The protocol for the skip connections.
        waveletType = neuralOperatorParameters['waveletType']  # The type of wavelet to use for the wavelet transform.

        # Hardcoded parameters.
        numDecompositions = 1  # Number of decompositions for the waveletType transform.
        mode = 'periodization'  # Mode for the waveletType transform.

        # Specify the default parameters.
        if numDecompositions is None: numDecompositions = min(5, waveletNeuralOperatorLayer.max_decompositions(signal_length=self.sequenceLength, wavelet_name=waveletType))  # Number of decompositions for the waveletType transform.

        return waveletNeuralOperatorLayer(sequenceLength=self.sequenceLength, numInputSignals=self.numInputSignals, numOutputSignals=self.numOutputSignals, numDecompositions=numDecompositions,
                                          waveletType=waveletType, mode=mode, addBiasTerm=self.addBiasTerm, activationMethod='none', skipConnectionProtocol=skipConnectionProtocol,
                                          encodeLowFrequencyProtocol=encodeLowFrequencyProtocol, encodeHighFrequencyProtocol=encodeHighFrequencyProtocol, learningProtocol=self.learningProtocol)
