import http
import ruamel.yaml
import requests
from service_environment import ServiceEnvironment
from neo4j_database import Neo4jDatabase
from datetime import date
from cosmos_conversion import convert_to_cosmos_bc_concept, convert_to_cosmos_sdtm_specialization

#Specify the date of this package to be delivered to CDISC
#package_date = '2023-09-01'
today = date.today()
package_date = today.strftime("%Y-%m-%d")
db = Neo4jDatabase()
sdtm_version='3.2'

#removing all activities with antibodies and removing AE requiring additional data
activityList_query="""
MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(p_asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(p_agrp:ActivityGroupValue),(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue)-[R6:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem), (p_ai)<-[:LATEST]-(x)
,(p_aitm1)<-[R8:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(p_aitmc1:ActivityItemClassValue) where p_aitmc1.name in ['concept_id','test_name_code'] and not p_agrp.name in ['AE Requiring Additional Data','Transthoracic Echocardiogram (TTE)','Clinical Outcome Assessments'] and not toLower(p_asgrp.name) contains 'anti'
return distinct p_act.name as activity_list
"""
activity_list  = db.graph().run(activityList_query).data()

#activity_list2 = [{'activity_list': 'Waist Circumference'},{'activity_list':'Glucose'},{'activity_list':'Mean Heart Rate by Electrocardiogram'}]
number = 1
desired_width = 6

for a in activity_list:
    print('Activity:',a['activity_list'])
    activity = a['activity_list'].replace("'", "\\'")
    print(activity)
    
    cosmos_bc = convert_to_cosmos_bc_concept(activity)
    cosmos_sdtm_bc= convert_to_cosmos_sdtm_specialization(activity, sdtm_version)
    
    for cbc in cosmos_bc:
   
        dom = cbc['activity']['domain'].lower()
    
        #if the conceptId were null it was set to UNKNOWN (C17998)
        if cbc['activity']['conceptId']=='C17998':
            #first convert the number to string then use zfil method
            number_str = str(number).zfill(desired_width) 
            concept_id = 'NEW_'+number_str   
            bc_file_name = 'biomedical_concept_'+dom+'_'+ concept_id
            number = number+1
            print('Filename: ',bc_file_name)
        
            bc = {}
            bc = {
                    'packageDate': package_date,
                    'packageType': cbc['activity']['packageType'],
                    'conceptId': concept_id,
                    'ncitCode': None,
                    'href': None,
                    'parentConceptId': None,
                    'categories':cbc['activity']['category'],
                    'shortName': cbc['activity']['activityName'],
                    'synonyms': None,
                    'resultScales': cbc['activity']['resultScale'],
                    'definition': None,
                    'dataElementConcepts': []
                }
            bc['dataElementConcepts'] = []
            if cbc['activity']['dataElementConcepts'] is not None:
                    for var in cbc['activity']['dataElementConcepts']:
                        if var['shortName'].upper() not in ['DOMAIN']:
                            print('VARNAME added: '+var['shortName'])
                            v = { 'conceptId': var['conceptId'],
                            'ncitCode': var['conceptId'],
                            'href': var['href'],
                            'shortName' :var['shortName'],
                            'dataType' : var['dataType'],
                            'exampleSet':var['exampleSet'] 
                            }
                            bc['dataElementConcepts'].append(v)
                
            path = 'nn_converted_data/bc_to_cdisc/'
            if bc_file_name is not None:
                filename = path+bc_file_name+'.yaml'
                with open(filename, 'w') as file:
                    yaml = ruamel.yaml.YAML()
                    yaml.indent(sequence=4, offset=2)
                    yaml.dump(bc, file)
            
            #The SDTM specializsations       
            for sbc in cosmos_sdtm_bc:
                sdtm_bc_file_name = 'nn_sdtm_bc_specialization_'+dom+'_'+sbc['activity']['datasetSpecializationId'].lower()
                print(sdtm_bc_file_name)
                bc_sdtm = {}
                bc_sdtm = {
                'packageDate': package_date,
                'packageType': sbc['activity']['packageType'],
                'domain': sbc['activity']['domain'],
                'shortName': sbc['activity']['shortName'],
                'datasetSpecializationId': sbc['activity']['datasetSpecializationId'],
                'source': sbc['activity']['source'],
                'sdtmigStartVersion': sbc['activity']['sdtmigStartVersion'],
                'sdtmigEndVersion': sbc['activity']['sdtmigEndVersion'],
                'biomedicalConceptId': concept_id,
                'variables': sbc['activity']['variables']
                }            

                path = 'nn_converted_data/sdtm/'
                if sdtm_bc_file_name is not None:
                    filename = path+sdtm_bc_file_name+'.yaml'
                    with open(filename, 'w') as file:
                        yaml = ruamel.yaml.YAML()
                        yaml.indent(sequence=4, offset=2)
                        yaml.dump(bc_sdtm, file)
                
            
        else:
            bc_file_name = 'biomedical_concept_'+dom+'_'+cbc['activity']['conceptId']
            print('Filename: ',bc_file_name)
            bc = {}
            bc = {
                'packageDate': package_date,
                'packageType': cbc['activity']['packageType'],
                'conceptId': cbc['activity']['conceptId'],
                'ncitCode': cbc['activity']['conceptId'],
                'href': cbc['activity']['href'],
                'parentConceptId': cbc['activity']['parentConceptId'],
                'categories':cbc['activity']['category'],
                'shortName': cbc['activity']['shortName'],
                'synonyms': cbc['activity']['synonym'],
                'resultScales': cbc['activity']['resultScale'],
                'definition': cbc['activity']['definition'],
                'dataElementConcepts': []
            }
            bc['dataElementConcepts'] = []
            if cbc['activity']['dataElementConcepts'] is not None:
                for var in cbc['activity']['dataElementConcepts']:
                    if var['shortName'].upper() not in ['DOMAIN']:
                        print('VARNAME added: '+var['shortName'])
                        v = { 'conceptId': var['conceptId'],
                        'ncitCode': var['conceptId'],
                        'href': var['href'],
                        'shortName' :var['shortName'],
                        'dataType' : var['dataType'],
                        'exampleSet':var['exampleSet'] 
                        }
                        bc['dataElementConcepts'].append(v)
        
            path = 'nn_converted_data/bc_to_cdisc/'  
            if bc_file_name is not None:
                filename = path+bc_file_name+'.yaml'
            with open(filename, 'w') as file:
                yaml = ruamel.yaml.YAML()
                yaml.indent(sequence=4, offset=2)
                yaml.dump(bc, file)
                
            #The SDTM specializsations
            for sbc in cosmos_sdtm_bc:
                sdtm_bc_file_name = 'nn_sdtm_bc_specialization_'+dom+'_'+sbc['activity']['datasetSpecializationId'].lower()
                print('Filename: ',sdtm_bc_file_name)
                bc_sdtm = {}
                bc_sdtm = {
                        'packageDate': package_date,
                        'packageType': sbc['activity']['packageType'],
                        'domain': sbc['activity']['domain'],
                        'shortName': sbc['activity']['shortName'],
                        'datasetSpecializationId': sbc['activity']['datasetSpecializationId'],
                        'source': sbc['activity']['source'],
                        'sdtmigStartVersion': sbc['activity']['sdtmigStartVersion'],
                        'sdtmigEndVersion': sbc['activity']['sdtmigEndVersion'],
                        'biomedicalConceptId': sbc['activity']['biomedicalConceptId'],
                        'variables': sbc['activity']['variables']
                }
            
                path = 'nn_converted_data/sdtm/'
                if sdtm_bc_file_name is not None:
                    filename = path+sdtm_bc_file_name+'.yaml'
                    with open(filename, 'w') as file:
                        yaml = ruamel.yaml.YAML()
                        yaml.indent(sequence=4, offset=2)
                        yaml.dump(bc_sdtm, file)

                    
              



    
