import requests
from service_environment import ServiceEnvironment
from neo4j_database import Neo4jDatabase
import pandas as pd
import numpy as np

db = Neo4jDatabase()

def search_cdisc_code_type_match(ccode):
    #MATCH on code/term for property=Contributing_Source where value=CDISC
    url ="https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/search?ascending=true&fromRecord=0&include=minimal&pageSize=10&property=Contributing_Source&term="+ccode+"&type=match&value=CDISC"
       
    r = requests.get(url)
    concept_info = r.json()
    if 'concepts' in concept_info:
     nci_code =concept_info['concepts'][0]['code']
     term=concept_info['concepts'][0]['name']
    else:
        nci_code=np.nan
        term=np.nan
    return nci_code,term

def search_cdisc_code_type_and(ccode):
    #MATCH on code/term for property=Contributing_Source where value=CDISC
    #Use the AND operator for searching.
    url ="https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/search?ascending=true&fromRecord=0&include=minimal&pageSize=10&property=Contributing_Source&term="+ccode+"&type=AND&value=CDISC"
       
    r = requests.get(url)
    concept_info = r.json()
    if 'concepts' in concept_info:
     nci_code =concept_info['concepts'][0]['code']
     term=concept_info['concepts'][0]['name']
    else:
        nci_code=np.nan
        term=np.nan
    return nci_code,term

def search_cdisc_code_type_contains(ccode):
    #MATCH on code/term for property=Contributing_Source where value=CDISC
    #match on contains and returns top 3 c-codes.
    #To return more choices then change pageSize=3 to another number.
    url ="https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/search?ascending=true&fromRecord=0&include=minimal&pageSize=3&property=Contributing_Source&term="+ccode+"&type=contains&value=CDISC"
    
    possible_nci_code_list=[]
    r = requests.get(url)
    concept_info = r.json()
    if 'concepts' in concept_info:
        for concept in concept_info['concepts']:
            possible_nci_code_list.append(concept['code']+' : '+ concept['name'])
    return possible_nci_code_list

#print(search_cdisc_code_type_contains("How%20Often%20During%20Last%20Year%20not%20Able%20Stop%20Drinking%20Once%20Started"))

query = """
MATCH (p_agrp:ActivityGroupValue)<-[R1:IN_GROUP]-(p_asgrp:ActivitySubGroupValue)<-[R2:IN_SUB_GROUP]-(p_act:ActivityValue)<-[R3:IN_HIERARCHY]-(p_ai:ActivityInstanceValue)-[R4:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItemValue) 
MATCH(p_aitm1)<-[R5:LATEST]-(p_aitm1r:ActivityItemRoot)<-[R6:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[R7:LATEST]->(p_aitmc1:ActivityItemClassValue)
OPTIONAL MATCH (p_ai)-[R8:ACTIVITY_INSTANCE_CLASS]->(p_aicr:ActivityInstanceClassRoot)-[R9:LATEST]->(p_aic:ActivityInstanceClassValue)
with p_aic.name as instanceType, p_agrp.name as group, p_asgrp.name as subgroup, p_act.name  as activity, p_ai.name as instance, apoc.coll.sort(collect(p_aitmc1.name)) as items where not 'test_name_code' in items
return distinct instanceType, group, subgroup, activity, instance, items order by instanceType, instance
"""

activity_list = db.graph().run(query).data()
df = pd.DataFrame(activity_list)
#print(len(df.index))
cat=['Clinical Outcome Assessments']
#If activity name is repeated in the instance name (for the Clinical  Outcome Assessments), then replace with blank, i.e. remove it, expect if the activity and instance has same name.
df['term'] = df.apply(lambda x: x['instance'].replace(x['activity'], '') if (x['instance']!=x['activity']) & (x['group']==cat) else x['instance'], axis=1)
#fix for 'ASCQ-Me type instances'
df['term'] = df.apply(lambda x: x['instance'].replace('ASCQ-Me', '') if ('ASCQ-Me' in x['activity'])  else x['term'], axis=1)
#fix for 'The Alcohol Use Disorders Identification Test (AUDIT-I)'
df['term'] = df.apply(lambda x: x['instance'].replace('AUDIT-I', '') if (x['activity']=='The Alcohol Use Disorders Identification Test (AUDIT-I)')  else x['term'], axis=1)
#for all activities in Clinical Outcome Assessment - split on '-' and use the last part of the term
df['search_term'] = df['term'].where((~df['group'].isin(cat)), other=[x.split("-", 1)[-1] for x in df['term']])
#Replace  space and colon with URL encodings
df['search_term_non_converted']=df['search_term']
df['search_term'] = df['search_term'].str.strip().str.replace(' ', '%20').str.replace(':','%3A')
#add empty column for the result
df['concept_id'] = np.nan

print(df.head(10))
#subset dataframe for testing
#df = df.head(10)

#Look for CDISC c-code based on search string - 1st pass to get exact CDISC matches (using MATCH)
arr = np.array(range(0, len(df['search_term'])-1))
for row in arr:
    if pd.notna(df.iloc[row]['search_term']) & pd.isna(df.iloc[row]['concept_id']):
        print('1st pass %s',df.iloc[row]['search_term'])
        result=search_cdisc_code_type_match(df.iloc[row]['search_term'])
        df.at[row, 'concept_id'] = result[0]
        df.at[row, 'nci_term'] = result[1]
# 2nd pass looks for all words (AND)
for row in arr:
    if pd.notna(df.iloc[row]['search_term']) & pd.isna(df.iloc[row]['concept_id']):
        print('2nd pass %s',df.iloc[row]['search_term'])
        result=search_cdisc_code_type_and(df.iloc[row]['search_term'])
        df.at[row, 'concept_id'] = result[0]
        df.at[row, 'nci_term'] = result[1]

# 3rd pass looks for any words (contains) and returns first 3 hits
for row in arr:
    if pd.notna(df.iloc[row]['search_term']) & pd.isna(df.iloc[row]['concept_id']):
        print('3rd pass %s',df.iloc[row]['search_term'])
        if len(search_cdisc_code_type_contains(df.iloc[row]['search_term'])):
            df.at[row, 'Top_3_possible_codes']=','.join(search_cdisc_code_type_contains(df.iloc[row]['search_term']))
        
print(df.head(10))
df.to_excel("output/activity_concept_id_missing_suggestion.xlsx") 
print('File written to output folder')

