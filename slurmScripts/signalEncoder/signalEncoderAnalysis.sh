#!/bin/sh
start=$(date +%s)

# Pass the parameters to the Python script
srun accelerate launch ./../../metaTrainingControl.py \
    --numSharedEncoderLayers "$1" \
    --numSpecificEncoderLayers "$2" \
    --encodedDimension "$3" \
    --deviceListed "HPC-$4" \
    --submodel "signalEncoderModel" \
    --waveletType "$5" \
    --optimizerType "$6" \
    --physioLR "$7" \
    --generalLR "$8" \
    --numEncodedWeights "$9" \
    --generalWD "${10}" \
    --physioWD "${11}"

end=$(date +%s)
runtime=$((end-start))
echo "Runtime: $runtime seconds"
