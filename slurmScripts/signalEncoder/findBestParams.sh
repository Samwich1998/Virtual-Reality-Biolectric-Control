#!/bin/bash

# General parameters: 18
allNumEncodedWeights=(2 4 8 16 32 64 128 256)  # 8
numSpecificEncoderLayers_arr=(1 2)  # 2
signalEncoderLayers_arr=(2 4 8 16 24 32)  # 6
encodedDimensions_arr=(64 128 256 512)  # 4

# General parameters: 18
allNumEncodedWeights=(64)  # 6
numSpecificEncoderLayers_arr=(1)  # 1
signalEncoderLayers_arr=(8)  # 3
encodedDimensions_arr=(256)  # 1

# Learning rates: 6
lrs_general=('1e-2' '1e-3' '1e-4')  # 2
lrs_physio=('100' '10' '1' '1e-1' '1e-2' '1e-3')  # 3

# Weight decays: 6
wds_general=('1e-1' '1e-2' '1e-3' '1e-4' '1e-5')  # 6
wds_physio=('1e-1' '1e-2' '1e-3' '1e-4' '1e-5')  # 6

# Finalized parameters.
waveletTypes_arr=('bior3.1')  # 'bior3.1' > 'bior3.3' > 'bior2.2' > 'bior3.5'
optimizers_arr=('RAdam')


for numEncodedWeights in "${allNumEncodedWeights[@]}"
do
  for lr_physio in "${lrs_physio[@]}"
  do
    for wd_general in "${wds_general[@]}"
    do
      for wd_physio in "${wds_physio[@]}"
      do
        for lr_general in "${lrs_general[@]}"
        do
          for optimizer in "${optimizers_arr[@]}"
          do
            for waveletType in "${waveletTypes_arr[@]}"
            do
              for encodedDimension in "${encodedDimensions_arr[@]}"
              do
                for numSpecificEncoderLayers in "${numSpecificEncoderLayers_arr[@]}"
                do
                  for numSharedEncoderLayers in "${signalEncoderLayers_arr[@]}"
                  do
                    # Check if numSpecificEncoderLayers is greater than half the numSharedEncoderLayers
                    if [ $((2 * numSpecificEncoderLayers)) -gt "$numSharedEncoderLayers" ]; then
                      continue  # Skip this iteration if the condition is true
                    fi

                    echo "Submitting job with $numSharedEncoderLayers numSharedEncoderLayers, $numSpecificEncoderLayers numSpecificEncoderLayers, $encodedDimension encodedDimension, $waveletType waveletType, $optimizer optimizer, $lr_physio lr_physio, $lr_general lr_general"

                    if [ "$1" == "CPU" ]; then
                        sbatch -J "signalEncoder_numSharedEncoderLayers_${numSharedEncoderLayers}_numSpecificEncoderLayers_${numSpecificEncoderLayers}_encodedDimension_${encodedDimension}_${waveletType}_${optimizer}_$1" submitSignalEncoder_CPU.sh "$numSharedEncoderLayers" "$numSpecificEncoderLayers" "$encodedDimension" "$1" "$waveletType" "$optimizer" "$lr_physio" "$lr_general" "$numEncodedWeights" "$wd_general" "$wd_physio"
                    elif [ "$1" == "GPU" ]; then
                        sbatch -J "signalEncoder_numSharedEncoderLayers_${numSharedEncoderLayers}_numSpecificEncoderLayers_${numSpecificEncoderLayers}_encodedDimension_${encodedDimension}_${waveletType}_${optimizer}_$1" submitSignalEncoder_GPU.sh "$numSharedEncoderLayers" "$numSpecificEncoderLayers" "$encodedDimension" "$1" "$waveletType" "$optimizer" "$lr_physio" "$lr_general" "$numEncodedWeights" "$wd_general" "$wd_physio"
                    else
                        echo "No known device listed: $1"
                    fi
                  done
                done
              done
            done
          done
        done
      done
    done
  done
done
