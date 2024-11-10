#!/bin/bash

encodedDimensions=(64 128)
# Total: 2

goldenRatios=(1 2 4 8)
# Total: 4

signalEncoderLayers=(1 2 4 8)
# Total: 4

waveletType="bior3.7"
optimizer="NAdam"     # Replace with actual value

for encodedDimension in "${encodedDimensions[@]}"
do
  for goldenRatio in "${goldenRatios[@]}"
  do
    for numSignalEncoderLayers in "${signalEncoderLayers[@]}"
    do
      # Check if goldenRatio is greater than numSignalEncoderLayers
      if [ "$goldenRatio" -gt "$numSignalEncoderLayers" ]; then
          continue  # Skip this iteration if the condition is true
      fi

      echo "Submitting job with $numSignalEncoderLayers numSignalEncoderLayers, $goldenRatio goldenRatio, $encodedDimension encodedDimension on $1"

      if [ "$1" == "CPU" ]; then
          sbatch -J "signalEncoder_numSignalEncoderLayers_${numSignalEncoderLayers}_goldenRatio_${goldenRatio}_encodedDimension_${encodedDimension}_${waveletType}_${optimizer}_$1" submitSignalEncoder_CPU.sh "$numSignalEncoderLayers" "$goldenRatio" "$encodedDimension" "$1" "$waveletType" "$optimizer"
      elif [ "$1" == "GPU" ]; then
          sbatch -J "signalEncoder_numSignalEncoderLayers_${numSignalEncoderLayers}_goldenRatio_${goldenRatio}_encodedDimension_${encodedDimension}_${waveletType}_${optimizer}_$1" submitSignalEncoder_GPU.sh "$numSignalEncoderLayers" "$goldenRatio" "$encodedDimension" "$1" "$waveletType" "$optimizer"
      else
          echo "No known device listed: $1"
      fi
    done
  done
done
