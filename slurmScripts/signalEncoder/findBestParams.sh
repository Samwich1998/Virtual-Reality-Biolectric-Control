#!/bin/bash

waveletTypes=('bior3.7')
optimizers=('RAdam')
encodedDimensions=(64 128)
signalEncoderLayers=(4 8 16 32)
weightDecays=(0.001)
goldenRatios=(1 2 4 8 16 32)
lrs=(0.01)

for optimizer in "${optimizers[@]}"
do
  for waveletType in "${waveletTypes[@]}"
  do
    for encodedDimension in "${encodedDimensions[@]}"
    do
      for goldenRatio in "${goldenRatios[@]}"
      do
        for numSignalEncoderLayers in "${signalEncoderLayers[@]}"
        do
          for lr in "${lrs[@]}"
          do
            for weightDecay in "${weightDecays[@]}"
            do
              # Check if goldenRatio is greater than numSignalEncoderLayers
              if [ "$goldenRatio" -gt "$numSignalEncoderLayers" ]; then
                  continue  # Skip this iteration if the condition is true
              fi

              echo "Submitting job with $numSignalEncoderLayers numSignalEncoderLayers, $goldenRatio goldenRatio, $encodedDimension encodedDimension, $waveletType waveletType, $optimizer optimizer, $lr lr, $weightDecay weightDecay on $1"

              if [ "$1" == "CPU" ]; then
                  sbatch -J "signalEncoder_numSignalEncoderLayers_${numSignalEncoderLayers}_goldenRatio_${goldenRatio}_encodedDimension_${encodedDimension}_${waveletType}_${optimizer}_$1" submitSignalEncoder_CPU.sh "$numSignalEncoderLayers" "$goldenRatio" "$encodedDimension" "$1" "$waveletType" "$optimizer" "$lr" "$weightDecay"
              elif [ "$1" == "GPU" ]; then
                  sbatch -J "signalEncoder_numSignalEncoderLayers_${numSignalEncoderLayers}_goldenRatio_${goldenRatio}_encodedDimension_${encodedDimension}_${waveletType}_${optimizer}_$1" submitSignalEncoder_GPU.sh "$numSignalEncoderLayers" "$goldenRatio" "$encodedDimension" "$1" "$waveletType" "$optimizer" "$lr" "$weightDecay"
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
