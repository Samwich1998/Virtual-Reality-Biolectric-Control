import torch.optim as optim
from torch.optim import Optimizer
from torch.optim.lr_scheduler import LRScheduler, _warn_get_lr_called_within_step

from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.modelConstants import modelConstants


class optimizerMethods:

    def __init__(self, userInputParams):
        # Set the user input parameters.
        self.userInputParams = userInputParams

    def getModelParams(self, submodel, model):
        modelParams = [
            # Specify the model parameters for the shared signal encoding.
            {'params': (param for name, param in model.sharedSignalEncoderModel.named_parameters() if "physiologicalGenerationModel" not in name), 'weight_decay': self.userInputParams['reversibleWD'], 'lr': self.userInputParams['reversibleLR']},  # 1e-6 - 1e-2
            {'params': model.sharedSignalEncoderModel.physiologicalGenerationModel.parameters(), 'weight_decay': self.userInputParams['physGenWD'], 'lr': self.userInputParams['physGenLR']},  # 1e-2 - 1e2

            # Specify the model parameters for the specific signal encoding.
            {'params': (param for name, param in model.specificSignalEncoderModel.named_parameters() if "profileModel" not in name), 'weight_decay': self.userInputParams['reversibleWD'], 'lr': self.userInputParams['reversibleLR']},  # 1e-2 - 1e2
            {'params': model.specificSignalEncoderModel.profileModel.parameters(), 'weight_decay': self.userInputParams['profileWD'], 'lr': self.userInputParams['profileLR']},  # 0.1 - 0.01
        ]

        if submodel == modelConstants.emotionModel:
            modelParams.extend([
                # Specify the model parameters for the emotion prediction.
                {'params': model.specificEmotionModel.parameters(), 'weight_decay': 1e-6, 'lr': self.userInputParams["emotionLearningRate"]},
                {'params': model.sharedEmotionModel.parameters(), 'weight_decay': 1e-6, 'lr': self.userInputParams["emotionLearningRate"]},

                # Specify the model parameters for the human activity recognition.
                {'params': model.specificActivityModel.parameters(), 'weight_decay': 1e-6, 'lr': self.userInputParams["activityLearningRate"]},
                {'params': model.sharedActivityModel.parameters(), 'weight_decay': 1e-6, 'lr': self.userInputParams["activityLearningRate"]},
            ])

        return modelParams

    def addOptimizer(self, submodel, model):
        # Get the model parameters.
        modelParams = self.getModelParams(submodel, model)

        # Set the optimizer and scheduler.
        optimizer = self.setOptimizer(modelParams, lr=1e-5, weight_decay=1e-6, optimizerType=self.userInputParams["optimizerType"])
        scheduler = self.getLearningRateScheduler(optimizer)

        return optimizer, scheduler

    def setOptimizer(self, params, lr, weight_decay, optimizerType):
        return self.getOptimizer(optimizerType=optimizerType, params=params, lr=lr, weight_decay=weight_decay, momentum=0.5)

    @staticmethod
    def getLearningRateScheduler(optimizer):
        # Options:
        # Slow ramp up: transformers.get_constant_schedule_with_warmup(optimizer=self.optimizer, num_warmup_steps=30)
        # Cosine waveform: optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=20, eta_min=1e-8, last_epoch=-1)
        # Reduce on plateau (need further editing of loop): optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, mode='min', factor=0.5, patience=10, threshold=1e-4, threshold_mode='rel', cooldown=0, min_lr=0, eps=1e-08)
        # Defined lambda function: optim.lr_scheduler.LambdaLR(self.optimizer, lr_lambda=lambda_function); lambda_function = lambda epoch: (epoch/50) if epoch < -1 else 1
        # torch.optim.lr_scheduler.constrainedLR(optimizer, start_factor=0.3333333333333333, end_factor=1.0, total_iters=5, last_epoch=-1)
        return CosineAnnealingLR_customized(optimizer, numWarmupEpochs=10,  T_max=1, absolute_min_lr=1e-4, multiplicativeFactor=10, warmupFactor=2, last_epoch=-1)  # TODO:

    @staticmethod
    def getOptimizer(optimizerType, params, lr, weight_decay, momentum=0.9):
        # General guidelines:
        #     Common WD values: 1E-2 to 1E-6
        #     Common LR values: 1E-6 to 1

        if optimizerType == 'Adadelta':
            # Adadelta is an extension of Adagrad that seeks to reduce its aggressive, monotonically decreasing learning rate.
            # Use it when you don’t want to manually tune the learning rate.
            return optim.Adadelta(params, lr=lr, rho=0.9, eps=1e-06, weight_decay=weight_decay)
        elif optimizerType == 'Adagrad':
            # Adagrad adapts the learning rates based on the parameters. It performs well with sparse data.
            # Use it if you are dealing with sparse features or in NLP tasks. Not compatible with GPU?!?
            return optim.Adagrad(params, lr=lr, lr_decay=0, weight_decay=weight_decay, initial_accumulator_value=0.2, eps=1e-10)
        elif optimizerType == 'Adam':
            # Adam is a first-order gradient-based optimization of stochastic objective functions, based on adaptive estimates.
            # It's broadly used and suitable for most problems without much hyperparameter tuning.
            return optim.Adam(params, lr=lr, betas=(0.7, 0.9), weight_decay=weight_decay, amsgrad=False, maximize=False)
        elif optimizerType == 'AdamW':
            # AdamW modifies the way Adam implements weight decay, decoupling it from the gradient updates, leading to a more effective use of L2 regularization.
            # Use when regularization is a priority and particularly when fine-tuning pre-trained models.
            return optim.AdamW(params, lr=lr, betas=(0.7, 0.9), weight_decay=weight_decay, amsgrad=False, maximize=False)
        elif optimizerType == 'NAdam':  # TODO:
            # NAdam combines Adam with Nesterov momentum, aiming to combine the benefits of Nesterov and Adam.
            # Use in deep architectures where fine control over convergence is needed.

            # return optim.NAdam(params, lr=lr, betas=(0.95, 0.999), weight_decay=weight_decay, momentum_decay=0.004, decoupled_weight_decay=True)

            # return optim.NAdam(params, lr=lr, betas=(0.9, 0.999), weight_decay=weight_decay, momentum_decay=0.004, decoupled_weight_decay=True)
            # return optim.NAdam(params, lr=lr, betas=(0.7, 0.97), weight_decay=weight_decay, momentum_decay=0.001, decoupled_weight_decay=True)

            # return optim.NAdam(params, lr=lr, betas=(0.7, 0.9), weight_decay=weight_decay, momentum_decay=0.004, decoupled_weight_decay=True)
            return optim.NAdam(params, lr=lr, betas=(0.7, 0.97), weight_decay=weight_decay, momentum_decay=0.001, decoupled_weight_decay=True)

            # return optim.NAdam(params, lr=lr, betas=(0.8, 0.9), weight_decay=weight_decay, momentum_decay=0.001, decoupled_weight_decay=True)
            # return optim.NAdam(params, lr=lr, betas=(0.9, 0.9), weight_decay=weight_decay, momentum_decay=0.001, decoupled_weight_decay=True)
            # return optim.NAdam(params, lr=lr, betas=(0.95, 0.9), weight_decay=weight_decay, momentum_decay=0.001, decoupled_weight_decay=True)


            # return optim.NAdam(params, lr=lr, betas=(0.95, 0.97), weight_decay=weight_decay, momentum_decay=0.001, decoupled_weight_decay=True)
        elif optimizerType == 'RAdam':
            # RAdam (Rectified Adam) is an Adam variant that introduces a term to rectify the variance of the adaptive learning rate.
            # Use it when facing unstable or poor training results with Adam, especially in smaller sample sizes.
            return optim.RAdam(params, lr=lr, betas=(0.7, 0.9), weight_decay=weight_decay, decoupled_weight_decay=True)
        elif optimizerType == 'Adamax':
            # Adamax is a variant of Adam based on the infinity norm, proposed as a more stable alternative.
            # Suitable for embeddings and sparse graients.
            return optim.Adamax(params, lr=lr, betas=(0.7, 0.9), weight_decay=weight_decay)
        elif optimizerType == 'ASGD':
            # ASGD (Averaged Stochastic Gradient Descent) is used when you require robustness over a large number of epochs.
            # Suitable for larger-scale and less well-behaved problems; often used in place of SGD when training for a very long time.
            return optim.ASGD(params, lr=lr, lambd=0.0001, alpha=0.75, t0=1000000.0, weight_decay=weight_decay)
        elif optimizerType == 'LBFGS':
            # LBFGS is an optimizer that approximates the Broyden–Fletcher–Goldfarb–Shanno algorithm, which is a quasi-Newton method.
            # Use it for small datasets where the exact second-order Hessian matrix computation is possible. Maybe cant use optimizer.step()??
            return optim.LBFGS(params, lr=lr, max_iter=20, max_eval=None, tolerance_grad=1e-07, tolerance_change=1e-09, history_size=100, line_search_fn=None)
        elif optimizerType == 'RMSprop':
            # RMSprop is an adaptive learning rate method designed to solve Adagrad's radically diminishing learning rates.
            # It is well-suited to handle non-stationary data as in training neural networks.
            return optim.RMSprop(params, lr=lr, alpha=0.99, weight_decay=weight_decay, momentum=momentum, centered=False)
        elif optimizerType == 'Rprop':
            # Rprop (Resilient Propagation) uses only the signs of the gradients, disregarding their magnitude.
            # Suitable for batch training, where the robustness of noisy gradients and the size of updates matters.
            return optim.Rprop(params, lr=lr, etas=(0.5, 1.2), step_sizes=(1e-06, 50))
        elif optimizerType == 'SGD':
            # SGD (Stochastic Gradient Descent) is simple yet effective, suitable for large datasets.
            # Use with momentum for non-convex optimization; ideal for most cases unless complexities require adaptive learning rates.
            return optim.SGD(params, lr=lr, momentum=momentum, dampening=0, weight_decay=weight_decay, nesterov=True)
        else: assert False, f"No optimizer initialized: {optimizerType}"


class CosineAnnealingLR_customized(LRScheduler):
    def __init__(self, optimizer: Optimizer, T_max: int, absolute_min_lr: float, multiplicativeFactor: int, warmupFactor: int,  last_epoch: int = -1, numWarmupEpochs=0):
        self.multiplicativeFactor = multiplicativeFactor  # The multiplicative factor for the learning rate decay.
        self.absolute_min_lr = absolute_min_lr  # The absolute minimum learning rate to use.
        self.numWarmupEpochs = numWarmupEpochs  # The number of epochs to warm up the learning rate.
        self.warmupFactor = warmupFactor  # The factor to increase the learning rate during warmup.
        self.T_max = T_max  # The number of iterations before resetting the learning rate.

        # Call the parent class constructor
        super().__init__(optimizer, last_epoch)
        self.step()

    def get_lr(self):
        """Retrieve the learning rate of each parameter group."""
        _warn_get_lr_called_within_step(self)

        # Base case: learning rate is constant.
        if self.last_epoch <= self.numWarmupEpochs: self.updateStep(self.warmupFactor, self.base_lrs)
        return self.updateStep(self.multiplicativeFactor, self.base_lrs)

    def updateStep(self, multiplicativeFactor, base_lrs):
        # Apply decay to each base learning rate
        decay_factor = multiplicativeFactor ** -((self.T_max - self.last_epoch) % self.T_max)
        return [max(self.absolute_min_lr, base_lr * decay_factor) for base_lr in base_lrs]
