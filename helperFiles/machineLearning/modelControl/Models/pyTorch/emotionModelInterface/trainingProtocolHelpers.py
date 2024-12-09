# General
import random
import time

import torch

from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.emotionDataInterface import emotionDataInterface
# Helper classes.
from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.generalMethods.modelHelpers import modelHelpers
from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.modelConstants import modelConstants
from helperFiles.machineLearning.modelControl.Models.pyTorch.emotionModelInterface.emotionModel.emotionModelHelpers.modelParameters import modelParameters
from helperFiles.machineLearning.modelControl.Models.pyTorch.modelMigration import modelMigration


class trainingProtocolHelpers:

    def __init__(self, submodel, accelerator):
        # General parameters.
        self.submodelsSaving = modelParameters.getSubmodelsSaving(submodel)  # The submodels to save.
        self.sharedModelWeights = modelConstants.sharedModelWeights  # The shared model weights.
        self.profileEpochs = modelParameters.getProfileEpochs()  # The number of epochs for profile training.
        self.minEpochs_modelAdjustment = 1  # The minimum number of epochs before adjusting the model architecture.
        self.accelerator = accelerator
        self.unifiedLayerData = None
        self.numTrailingLosses = 2

        # Helper classes.
        self.modelMigration = modelMigration(accelerator)
        self.modelHelpers = modelHelpers()

    def trainEpoch(self, submodel, allMetadataLoaders, allMetaModels, allModels, allDataLoaders):
        # Set random order to loop through the models.
        self.unifyAllModelWeights(allMetaModels, allModels)
        modelIndices = list(range(len(allMetaModels)))
        random.shuffle(modelIndices)

        # For each training model.
        for modelInd in modelIndices:
            dataLoader = allMetadataLoaders[modelInd] if modelInd < len(allMetadataLoaders) else allDataLoaders[modelInd - len(allMetaModels)]  # Same pipeline instance in training loop.
            modelPipeline = allMetaModels[modelInd] if modelInd < len(allMetaModels) else allModels[modelInd - len(allMetaModels)]  # Same pipeline instance in training loop.
            trainSharedLayers = modelInd < len(allMetaModels)  # Train the shared layers.

            # Train the updated model.
            self.modelMigration.unifyModelWeights(allModels=[modelPipeline], modelWeights=self.sharedModelWeights, layerInfo=self.unifiedLayerData)
            modelPipeline.trainModel(dataLoader, submodel, profileTraining=False, specificTraining=True, trainSharedLayers=trainSharedLayers, stepScheduler=False, numEpochs=1)   # Full model training.
            self.accelerator.wait_for_everyone()

            # Unify all the model weights and retrain the specific models.
            modelPipeline.modelHelpers.roundModelWeights(modelPipeline.model, decimals=16)
            self.unifiedLayerData = self.modelMigration.copyModelWeights(modelPipeline, self.sharedModelWeights)

        # Unify all the model weights.
        self.unifyAllModelWeights(allMetaModels, allModels)
        self.datasetSpecificTraining(submodel, allMetadataLoaders, allMetaModels, allModels, allDataLoaders)

    def datasetSpecificTraining(self, submodel, allMetadataLoaders, allMetaModels, allModels, allDataLoaders):
        # Unify all the model weights.
        self.unifyAllModelWeights(allMetaModels, allModels)

        # For each meta-training model.
        for modelInd in range(len(allMetaModels) + len(allModels)):
            dataLoader = allMetadataLoaders[modelInd] if modelInd < len(allMetadataLoaders) else allDataLoaders[modelInd - len(allMetaModels)]  # Same pipeline instance in training loop.
            modelPipeline = allMetaModels[modelInd] if modelInd < len(allMetaModels) else allModels[modelInd - len(allMetaModels)]  # Same pipeline instance in training loop.
            if modelPipeline.datasetName.lower() == 'empatch': numEpochs = 2
            elif modelPipeline.datasetName.lower() == 'wesad': numEpochs = 8
            else: numEpochs = 1

            # Train the updated model.
            modelPipeline.trainModel(dataLoader, submodel, profileTraining=False, specificTraining=True, trainSharedLayers=False, stepScheduler=False, numEpochs=numEpochs)  # Signal-specific training.

            # Physiological profile training.
            modelPipeline.resetPhysiologicalProfile()
            numEpochs = modelPipeline.getTrainingEpoch(submodel)
            modelPipeline.trainModel(dataLoader, submodel, profileTraining=True, specificTraining=False, trainSharedLayers=False, stepScheduler=True, numEpochs=min(numEpochs + 1, self.profileEpochs))  # Profile training.
            self.accelerator.wait_for_everyone()

            with torch.no_grad():
                # Record final state paths.
                batchSignalInfo, _, _, _, _, _ = modelPipeline.extractBatchInformation(dataLoader.dataset.getAll())
                signalBatchData, batchSignalIdentifiers, metaBatchInfo = emotionDataInterface.separateData(batchSignalInfo)
                modelPipeline.model.fullPass(submodel, signalBatchData, batchSignalIdentifiers, metaBatchInfo, device=modelPipeline.accelerator.device, onlyProfileTraining=True)
            self.accelerator.wait_for_everyone()

    def calculateLossInformation(self, allMetadataLoaders, allMetaModels, allModels, allDataLoaders, submodel):
        self.unifyAllModelWeights(allMetaModels, allModels)  # Unify all the model weights.

        t1 = time.time()
        # For each meta-training model.
        for modelInd in range(len(allMetaModels) + len(allModels)):
            lossDataLoader = allMetadataLoaders[modelInd] if modelInd < len(allMetadataLoaders) else allDataLoaders[modelInd - len(allMetaModels)]  # Same pipeline instance in training loop.
            modelPipeline = allMetaModels[modelInd] if modelInd < len(allMetaModels) else allModels[modelInd - len(allMetaModels)]  # Same pipeline instance in training loop.

            # Calculate and store all the training and testing losses of the untrained model.
            with torch.no_grad(): modelPipeline.organizeLossInfo.storeTrainingLosses(submodel, modelPipeline, lossDataLoader)
        t2 = time.time(); self.accelerator.print("Total loss calculation time:", t2 - t1)

    def plotModelState(self, allMetadataLoaders, allMetaModels, allModels, allDataLoaders, submodel, trainingDate):
        self.unifyAllModelWeights(allMetaModels, allModels)  # Unify all the model weights.

        t1 = time.time()
        # For each meta-training model.
        for modelInd in range(len(allMetaModels) + len(allModels)):
            lossDataLoader = allMetadataLoaders[modelInd] if modelInd < len(allMetadataLoaders) else allDataLoaders[modelInd - len(allMetaModels)]  # Same pipeline instance in training loop.
            modelPipeline = allMetaModels[modelInd] if modelInd < len(allMetaModels) else allModels[modelInd - len(allMetaModels)]  # Same pipeline instance in training loop.

            with torch.no_grad():
                numEpochs = modelPipeline.getTrainingEpoch(submodel)
                modelPipeline.modelVisualization.plotAllTrainingEvents(submodel, modelPipeline, lossDataLoader, trainingDate, numEpochs)
        with torch.no_grad(): allMetaModels[0].modelVisualization.plotDatasetComparison(submodel, allMetaModels + allModels, trainingDate)
        t2 = time.time()
        self.accelerator.print("Total plotting time:", t2 - t1)

    def saveModelState(self, epoch, allMetaModels, allModels, submodel, allDatasetNames, trainingDate):
        # Prepare to save the model.
        numEpochs = allMetaModels[-1].getTrainingEpoch(submodel) or epoch
        self.unifyAllModelWeights(allMetaModels, allModels)
        allPipelines = allMetaModels + allModels

        # Save the current version of the model.
        self.modelMigration.saveModels(modelPipelines=allPipelines, datasetNames=allDatasetNames, sharedModelWeights=self.sharedModelWeights, submodelsSaving=self.submodelsSaving,
                                       submodel=submodel, trainingDate=trainingDate, numEpochs=numEpochs, metaTraining=True, saveModelAttributes=True)

    def unifyAllModelWeights(self, allMetaModels=None, allModels=None):
        if self.unifiedLayerData is None: self.unifiedLayerData = self.modelMigration.copyModelWeights(allMetaModels[0], self.sharedModelWeights)

        # Unify all the model weights.
        if allMetaModels: self.modelMigration.unifyModelWeights(allModels=allMetaModels, modelWeights=self.sharedModelWeights, layerInfo=self.unifiedLayerData)
        if allModels: self.modelMigration.unifyModelWeights(allModels=allModels, modelWeights=self.sharedModelWeights, layerInfo=self.unifiedLayerData)
