import math

import torch
import torch.nn as nn

from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.submodels.modelComponents.reversibleComponents.reversibleInterface import reversibleInterface


def getActivationMethod(activationMethod):
    if activationMethod == 'Tanhshrink':
        activationFunction = nn.Tanhshrink()
    elif activationMethod.startswith('none'):
        activationFunction = nn.Identity()
    elif activationMethod.startswith('boundedExp'):
        nonLinearityRegion = int(activationMethod.split('_')[2]) if '_' in activationMethod else 2
        topExponent = int(activationMethod.split('_')[1]) if '_' in activationMethod else 0
        activationFunction = boundedExp(decayConstant=topExponent, nonLinearityRegion=nonLinearityRegion)
    elif activationMethod.startswith('reversibleLinearSoftSign'):
        invertedActivation = activationMethod.split('_')[1] == "True"
        activationFunction = reversibleLinearSoftSign(invertedActivation=invertedActivation)
    elif activationMethod.startswith('boundedS'):
        invertedActivation = activationMethod.split('_')[1] == "True"
        activationFunction = boundedS(invertedActivation=invertedActivation)
    elif activationMethod == 'PReLU':
        activationFunction = nn.PReLU()
    elif activationMethod == 'selu':
        activationFunction = nn.SELU()
    elif activationMethod == 'gelu':
        activationFunction = nn.GELU()
    elif activationMethod == 'relu':
        activationFunction = nn.ReLU()
    else: raise ValueError("Activation type must be in ['Tanhshrink', 'none', 'boundedExp', 'reversibleLinearSoftSign', 'boundedS', 'PReLU', 'selu', 'gelu', 'relu']")

    return activationFunction


class reversibleLinearSoftSign(reversibleInterface):
    def __init__(self, invertedActivation=False, linearity=7/4, infiniteBound=33/49, scalarAdjustment=1):
        super(reversibleLinearSoftSign, self).__init__()
        self.invertedActivation = invertedActivation  # Whether the non-linearity term is inverted
        self.scalarAdjustment = scalarAdjustment  # Scalar adjustment for numerical stability
        self.infiniteBound = infiniteBound  # This controls how the activation converges at +/- infinity; Ex: 0.5, 13/21, 33/49
        self.linearity = linearity  # Corresponds to `r` in the equation; Ex: 4/3, 3/2, 7/4
        self.tolerance = 1e-20  # Tolerance for numerical stability

        # Assert the validity of the inputs.
        assert 0 < self.linearity, "The inversion point must be positive to ensure a stable convergence."

    def forward(self, x):
        if self.forwardDirection != self.invertedActivation: return self.forwardPass(x)
        else: return self.inversePass(x)

    def forwardPass(self, x):
        x = x * self.scalarAdjustment  # Adjust the scalar for numerical stability
        return (self.infiniteBound*x + x / (1 + x.abs()) / self.linearity) / self.scalarAdjustment  # f(x) = x + x / (1 + |x|) / r

    def inversePass(self, y):
        # Prepare the terms for the inverse pass.
        signY = torch.nn.functional.hardtanh(y, min_val=-self.tolerance, max_val=self.tolerance) / self.tolerance
        r, a = self.linearity, self.infiniteBound  # The linearity and infinite bound terms
        y = y * self.scalarAdjustment  # Adjust the scalar for numerical stability

        sqrtTerm = ((r*a)**2 + 2*a*r*(1 + signY*y*r) + (r*y - signY).pow(2)) / (r*a)**2
        x = signY*(sqrtTerm.sqrt() - 1)/2 - signY / (2*a*r) + y / (2*a)

        return x / self.scalarAdjustment


class boundedS(reversibleInterface):
    def __init__(self, invertedActivation=False, linearity=2):
        super(boundedS, self).__init__()
        self.invertedActivation = invertedActivation  # Whether the non-linearity term is inverted
        self.linearity = linearity  # Corresponds to `r` in the equation
        self.tolerance = 1e-100  # Tolerance for numerical stability

        # Assert the validity of the inputs.
        assert 0 < self.linearity, "The linearity term must be positive."

    def forward(self, x):
        if self.forwardDirection != self.invertedActivation: return self.forwardPass(x)
        else: return self.inversePass(x)

    def forwardPass(self, x):
        return x + x / (1 + x.pow(2)) / self.linearity

    # TODO: unstable, diverges to infinity
    def inversePass(self, y):
        b, b2, b3 = self.linearity, self.linearity ** 2, self.linearity ** 3
        y2, y3, y4 = y.pow(2), y.pow(3), y.pow(4)

        # Compute components.
        term2 = 3 * b * (b + 1) - b2 * y2
        term1 = 2 * b3 * y3 + 18 * b3 * y - 9 * b2 * y
        N = term1 + torch.sqrt(torch.abs(4 * term2.pow(3) + term1.pow(2)))

        # Compute the cube root term
        signN = torch.nn.functional.hardtanh(N, min_val=-self.tolerance, max_val=self.tolerance) / self.tolerance
        cube_root_term = signN * (N.abs() + self.tolerance).pow(1 / 3)

        # Compute x using the given equation
        x = (cube_root_term / (3 * (2 ** (1 / 3)) * b)) - ((2 ** (1 / 3)) * term2) / (3 * b * cube_root_term + self.tolerance) + y / 3

        return x


class boundedExp(nn.Module):
    def __init__(self, decayConstant=0, nonLinearityRegion=2, infiniteBound=math.exp(-0.5)):
        super(boundedExp, self).__init__()
        # General parameters.
        self.nonLinearityRegion = nonLinearityRegion  # The non-linear region is mainly between [-nonLinearityRegion, nonLinearityRegion].
        self.infiniteBound = infiniteBound  # This controls how the activation converges at +/- infinity. The convergence is equal to inputValue*infiniteBound.
        self.decayConstant = decayConstant  # This controls the non-linearity of the data close to 0. Larger values make the activation more linear. Recommended to be 0 or 1. After 1, the activation becomes linear near 0.

        # Assert the validity of the inputs.
        assert isinstance(self.decayConstant, int), f"The decayConstant must be an integer to ensure a continuous activation, but got {type(self.decayConstant).__name__}"
        assert 0 < abs(self.infiniteBound) <= 1, "The magnitude of the inf bound has a domain of (0, 1] to ensure a stable convergence."
        assert 0 < self.nonLinearityRegion, "The non-linearity region must be positive, as negatives are redundant and 0 is linear."
        assert 0 <= self.decayConstant, "The decayConstant must be greater than 0 for the activation function to be continuous."

    def forward(self, x):
        # Calculate the exponential activation function.
        exponentialDenominator = 1 + torch.pow(x / self.nonLinearityRegion, 2 * self.decayConstant + 2)
        exponentialNumerator = torch.pow(x / self.nonLinearityRegion, 2 * self.decayConstant)
        exponentialTerm = torch.exp(exponentialNumerator / exponentialDenominator)

        # Calculate the linear term.
        linearTerm = self.infiniteBound * x

        return linearTerm * exponentialTerm


if __name__ == "__main__":
    # Test the activation functions
    data = torch.randn(2, 10, 100, dtype=torch.float64)
    data = data - data.min(dim=-1, keepdim=True).values
    data = data / data.max(dim=-1, keepdim=True).values
    data = 2 * data - 1

    # Perform the forward and inverse pass.
    activationClass = reversibleLinearSoftSign(invertedActivation=True)
    _forwardData, _reconstructedData = activationClass.checkReconstruction(data, atol=1e-6, numLayers=100)
