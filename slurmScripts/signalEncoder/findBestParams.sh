#!/bin/bash

# Optimizer parameters.
optimizers_arr=('NAdam' 'AdamW' 'RAdam' 'Adam')  # AdamW == NAdam > RAdam > Adam > Adamax
momentums_arr=('0.004')  # Removed from filename
beta1s_arr=('0.7')  # Removed from filename
beta2s_arr=('0.9')  # Removed from filename

# Weight decay parameters.
wds_profile=('1e-6')  # 1e-6 ==> x <== 1e-3; Removed from filename
wds_profileGen=('1e-5')  # 1e-5 == x <= 1e-4; Removed from filename
wds_reversible=('1e-4')  # 1e-4 == x <= 1e-3; Removed from filename

# Known interesting parameters: 128
numSharedEncoderLayers_arr=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)  # 16
numSpecificEncoderLayers_arr=(1 2 3 4 5 6 7 8)  # 8

# Known interesting parameters: 256 -> 208
allNumEncodedWeights=(4 8 16 32 64 128 256 512)  # 8
numProfileShots_arr=(1 2 3 4 8 16 24 32)  # 8
encodedDimensions_arr=(64 128 256 512)  # 4
initialProfileAmp_arr=('0.01')  # 0.005 <= x <= 0.05

# Neural operator parameters.
waveletTypes_arr=('bior3.1' 'bior3.3' 'bior3.5' 'bior2.2')  # 'bior3.1' > 'bior3.3' > 'bior2.2' > 'bior3.5'
waveletTypes_arr=(
    # 15 bior wavelets
    'bior1.1' 'bior1.3' 'bior1.5' 'bior2.2' 'bior2.4' 'bior2.6' 'bior2.8' \
    'bior3.1' 'bior3.3' 'bior3.5' 'bior3.7' 'bior3.9' 'bior4.4' 'bior5.5' 'bior6.8' \
)

# Learning parameters.
lrs_profile=('0.005' '0.0075' '0.01' '0.02' '0.03' '0.04' '0.05')  # 0.005 <= x <= 0.05
lrs_profileGen=('1e-4') # # 5e-5 <= x == 1e-4; Removed from filename
lrs_reversible=('1e-3')  # 1e-4 <= x == 1e-3; Removed from filename

# Collective Switchables: 128
numSpecificEncoderLayers_arr=(1)
numSharedEncoderLayers_arr=(6)

# Collective Switchables: 256
encodedDimensions_arr=(256)
allNumEncodedWeights=(128)
numProfileShots_arr=(16)

# Single Switchables.
waveletTypes_arr=('bior3.1')
optimizers_arr=('NAdam')
#lrs_profile=('0.01')

for beta1s in "${beta1s_arr[@]}"
do
  for beta2s in "${beta2s_arr[@]}"
  do
    for momentums in "${momentums_arr[@]}"
    do
      for numEncodedWeights in "${allNumEncodedWeights[@]}"
      do
        for initialProfileAmp in "${initialProfileAmp_arr[@]}"
        do
          for numProfileShots in "${numProfileShots_arr[@]}"
          do
            for lr_profile in "${lrs_profile[@]}"
            do
              for wd_reversible in "${wds_reversible[@]}"
              do
                for wd_profile in "${wds_profile[@]}"
                do
                  for lr_reversible in "${lrs_reversible[@]}"
                  do
                    for wd_profileGen in "${wds_profileGen[@]}"
                    do
                      for lr_profileGen in "${lrs_profileGen[@]}"
                      do
                        for optimizer in "${optimizers_arr[@]}"
                        do
                          for waveletType in "${waveletTypes_arr[@]}"
                          do
                            for encodedDimension in "${encodedDimensions_arr[@]}"
                            do
                              for numSpecificEncoderLayers in "${numSpecificEncoderLayers_arr[@]}"
                              do
                                for numSharedEncoderLayers in "${numSharedEncoderLayers_arr[@]}"
                                do
                                  if (( encodedDimension < numEncodedWeights )); then
                                      continue
                                  fi
                                  
                                  if [ "$1" == "CPU" ]; then
                                      sbatch -J "signalEncoder_numSharedEncoderLayers_${numSharedEncoderLayers}_numSpecificEncoderLayers_${numSpecificEncoderLayers}_encodedDimension_${encodedDimension}_${waveletType}_${optimizer}_$1" submitSignalEncoder_CPU.sh "$numSharedEncoderLayers" "$numSpecificEncoderLayers" "$encodedDimension" "$numProfileShots" "$1" "$waveletType" "$optimizer" "$lr_profile" "$lr_reversible" "$lr_profileGen" "$numEncodedWeights" "$wd_profile" "$wd_reversible" "$wd_profileGen" "$beta1s" "$beta2s" "$momentums" "$initialProfileAmp"
                                  elif [ "$1" == "GPU" ]; then
                                      sbatch -J "signalEncoder_numSharedEncoderLayers_${numSharedEncoderLayers}_numSpecificEncoderLayers_${numSpecificEncoderLayers}_encodedDimension_${encodedDimension}_${waveletType}_${optimizer}_$1" submitSignalEncoder_GPU.sh "$numSharedEncoderLayers" "$numSpecificEncoderLayers" "$encodedDimension" "$numProfileShots" "$1" "$waveletType" "$optimizer" "$lr_profile" "$lr_reversible" "$lr_profileGen" "$numEncodedWeights" "$wd_profile" "$wd_reversible" "$wd_profileGen" "$beta1s" "$beta2s" "$momentums" "$initialProfileAmp"
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
            done
          done
        done
      done
    done
  done
done
