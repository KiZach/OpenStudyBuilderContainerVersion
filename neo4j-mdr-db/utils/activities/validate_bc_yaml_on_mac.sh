if test -f "bc_yaml_validation.log"; then
   rm bc_yaml_validation.log
fi

touch bc_yaml_validation.log
source .venv/bin/activate
for file in `ls nn_converted_data/bc_to_cdisc/*.yaml` ;do
 echo "Validating: "${file} | tee -a bc_yaml_validation.log
 linkml-validate -C BiomedicalConcept -s https://raw.githubusercontent.com/cdisc-org/COSMoS/main/model/cosmos_bc_model.yaml ${file} >&1 | tee -a bc_yaml_validation.log

done 
grep -i -n "error" bc_yaml_validation.log
deactivate

