if test -f "bc_sdtm_yaml_validation.log"; then
   rm bc_sdtm_yaml_validation.log
fi

touch bc_sdtm_yaml_validation.log
source .venv/bin/activate
for file in `ls nn_converted_data/sdtm/*.yaml` ;do
 echo "Validating: "${file} | tee -a bc_sdtm_yaml_validation.log
 linkml-validate -C SDTMGroup -s https://raw.githubusercontent.com/cdisc-org/COSMoS/main/model/cosmos_sdtm_bc_model.yaml ${file} >&1 | tee -a bc_sdtm_yaml_validation.log

done 
grep -i -n "error" bc_sdtm_yaml_validation.log
deactivate

