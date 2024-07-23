import requests
from service_environment import ServiceEnvironment
from neo4j_database import Neo4jDatabase
import pandas as pd
import numpy as np

db = Neo4jDatabase()

def get_hierarchy_root(ccode):
 url = 'https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/'+ccode+'/pathsFromRoot?fromRecord=0&pageSize=100'
 r = requests.get(url)
 concept_info = r.json()
 if not isinstance(concept_info, list):
     root ='None returned'
 else:
     root = concept_info[0][0]['name']
 return root

def check_if_cdisc_code(ccode):
    #MATCH on code/term for property=Contributing_Source where value=CDISC
    url ='https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/search?ascending=true&fromRecord=0&include=minimal&pageSize=10&property=Contributing_Source&term='+ccode+'&type=match&value=CDISC'
    r = requests.get(url)
    concept_info = r.json()
    if 'concepts' in concept_info:
     is_cdisc ='TRUE'
    else:
     is_cdisc = 'FALSE'
    return is_cdisc

#Get activities which have a C-code for the tet_name_code
query = """
MATCH (p_agrp:ActivityGroupValue)<-[R1:IN_GROUP]-(p_asgrp:ActivitySubGroupValue)<-[R2:IN_SUB_GROUP]-(p_act:ActivityValue)<-[R3:IN_HIERARCHY]-(p_ai:ActivityInstanceValue)-[R4:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItemValue) 
MATCH(p_aitm1)<-[R5:LATEST]-(p_aitm1r:ActivityItemRoot)<-[R6:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[R7:LATEST]->(p_aitmc1:ActivityItemClassValue) where p_aitmc1.name='test_name_code'
OPTIONAL MATCH (p_aitm1)-[R17]->(p_ct2cd:CTTermRoot)-[R18:HAS_NAME_ROOT]->(ct2cdr:CTTermNameRoot)-[R19:LATEST]->(p_ct2_sponsor), (p_ct2cd)-[R20:HAS_ATTRIBUTES_ROOT]->(ct2att:CTTermAttributesRoot)-[R21:LATEST]->(p_ct2_cdisc),(p_ct2cd)<-[R22:HAS_TERM]-(cl)-[R23:HAS_ATTRIBUTES_ROOT]->(clatt:CTCodelistAttributesRoot),(cl)-[R24:HAS_NAME_ROOT]->(clattr:CTCodelistNameRoot)-[:LATEST]-(p_cl_sponsor),(clatt)-[]->(p_cl_cdisc:CTCodelistAttributesValue)<-[]-(pc:CTPackageCodelist) WHERE pc.uid CONTAINS 'SDTM' 
WITH p_agrp.name as Group,
p_asgrp.name as SubGroup,
p_act.name as Activity,
p_ai.adam_param_code as Instance_adam_param_cd,
p_ai.topic_code as Instance_topic_cd,
coalesce(p_ct2_cdisc.concept_id,'NA') as concept_id,
coalesce(p_ct2_cdisc.preferred_term,p_ct2_sponsor) as term where not concept_id='NA'
return distinct
Group, SubGroup, Activity,Instance_adam_param_cd, Instance_topic_cd, concept_id, term order by concept_id desc
"""

activity_list = db.graph().run(query).data()
df = pd.DataFrame(activity_list)
print(len(df.index) )
bcID = pd.DataFrame()
#get unique set of concept_ids
bcID['concept_id'] = df.concept_id.unique()
#find the Root for the concept_id
bcID['Root'] = bcID.apply(lambda row: get_hierarchy_root(row['concept_id']), axis = 1) 
bcID['IsCDISCcode'] = bcID.apply(lambda row: check_if_cdisc_code(row['concept_id']), axis = 1) 
#join back on the original dataframe
df = df.merge(bcID, on='concept_id', how='left')
print(df.head(10))
df.to_excel("output/activity_concept_id_findings_with_check.xlsx") 
print('File written to output folder')






