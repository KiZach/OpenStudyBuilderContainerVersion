import http
import yaml
import requests
from service_environment import ServiceEnvironment
from neo4j_database import Neo4jDatabase
from datetime import date

#Specify the date of this package to be delivered to CDISC
#package_date = '2023-09-01'
today = date.today()
package_date = today.strftime("%Y-%b-%d")
db = Neo4jDatabase()

def process_instances_nn_concept():
  #removing all activities with antibodies and removing AE requiring additional data
    activityList="""
    MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(p_asgrp:ActivitySubGroupValue),
    (sg)-[R4:IN_GROUP]->(p_agrp:ActivityGroupValue),(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue)-[R6:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem), (p_ai)<-[:LATEST]-(x)
    ,(p_aitm1)<-[R8:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(p_aitmc1:ActivityItemClassValue) where p_aitmc1.name in ['concept_id','test_name_code'] and not p_agrp.name='AE Requiring Additional Data' and not toLower(p_asgrp.name) contains 'anti'
    return distinct p_act.name as activity_list
    """
    
    activity_list  = db.graph().run(activityList).data()
    for a in activity_list:
        print('Activity: ',a['activity_list'])
        activity = a['activity_list'].replace("'", "\\'")
        print(activity)
        bc_query="""
        MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(p_asgrp:ActivitySubGroupValue),
        (sg)-[R4:IN_GROUP]->(p_agrp:ActivityGroupValue) where p_act.name ='"""+activity+"""'
        MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue)-[R6:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem),(p_ai)<-[:LATEST]-(x)
        MATCH (p_ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(p_aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(p_aic:ActivityInstanceClassValue)
        OPTIONAL MATCH(p_aitm1)<-[R8:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(p_aitmc1:ActivityItemClassValue)
        OPTIONAL MATCH (p_aicr)-[R10:PARENT_CLASS]->(p_aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(p_aicp:ActivityInstanceClassValue)
        OPTIONAL MATCH (p_aicrp)-[R12:PARENT_CLASS]->(p_aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(p_aicpp:ActivityInstanceClassValue)
        OPTIONAL MATCH(p_aitmc1r)<-[R14:HAS_ITEM_CLASS]-(p_aicr)
        OPTIONAL MATCH(p_aitmc1r)<-[R15:HAS_ITEM_CLASS]-(p_aicrp)
        OPTIONAL MATCH(p_aitmc1r)<-[R16:HAS_ITEM_CLASS]-(p_aicrpp) 
        OPTIONAL MATCH (p_aitm1)-[R17]->(p_ct2cd:CTTermRoot)-[R18:HAS_NAME_ROOT]->(ct2cdr:CTTermNameRoot)-[R19:LATEST]->(p_ct2_sponsor), (p_ct2cd)-[R20:HAS_ATTRIBUTES_ROOT]->(ct2att:CTTermAttributesRoot)-[R21:LATEST]->(p_ct2_cdisc)
        OPTIONAL MATCH (p_aitm1)-[:HAS_UNIT_DEFINITION]->(p_unitdefr:UnitDefinitionRoot)-[R22:LATEST]->(p_unitdef:UnitDefinitionValue)
        OPTIONAL MATCH(p_ct2cd)<-[R23:HAS_TERM]-(clr:CTCodelistRoot)-[R24:HAS_ATTRIBUTES_ROOT]->(clatt:CTCodelistAttributesRoot),(clr)-[R25:HAS_NAME_ROOT]->(clattr:CTCodelistNameRoot)-[R26:LATEST]-(p_cl_sponsor),(clatt)-[R27:LATEST]->(p_cl_cdisc:CTCodelistAttributesValue),(pc:CTPackageCodelist) where ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-(pc) and pc.uid CONTAINS "SDTM") or NOT ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-())
        OPTIONAL MATCH (p_unitdef:UnitDefinitionValue)-[R28:HAS_CT_DIMENSION]-(unit_term:CTTermRoot)<-[R29:HAS_TERM]-(cl_root)-[R30:HAS_ATTRIBUTES_ROOT]->(clattr2)-[R31:LATEST]->(unit_cld)
        OPTIONAL MATCH(p_aitmc1)-[R32:HAS_ROLE]->(p_role_r:CTTermRoot),(p_role_r)-[R33:HAS_NAME_ROOT]->(ctnr_role)-[R34:LATEST]->(p_role_val), (p_role_r)-[R35:HAS_ATTRIBUTES_ROOT]->(ctattr)-[R36:LATEST]->(p_role_attr_val)
        OPTIONAL MATCH(p_aitmc1)-[R37:HAS_DATA_TYPE]->(p_dtype_r),(p_dtype_r)-[R38:HAS_NAME_ROOT]->(ctnr_dtype)-[R39:LATEST]->(p_dtype_val), (p_dtype_r)-[R40:HAS_ATTRIBUTES_ROOT]->(ctattr_dtype)-[R41:LATEST]->(p_dtype_attr_val)
        with distinct p_act.name as ActivityName, p_aic as aic, p_asgrp as asgrp, p_aitmc1 as aitmc1,p_ai as ai,p_unitdef as unit_ct,
        CASE WHEN p_ct2cd is not null THEN apoc.map.merge(properties(p_ct2_cdisc),properties(p_ct2_sponsor)) END as ct2,
        CASE WHEN p_role_r is not null THEN apoc.map.merge(properties(p_role_val),properties(p_role_attr_val)) END as role,
        CASE WHEN p_dtype_r is not null THEN apoc.map.merge(properties(p_dtype_val),properties(p_dtype_attr_val)) END as dtype,
        CASE WHEN p_ct2cd is not null THEN apoc.map.merge(properties(p_cl_cdisc),properties(p_cl_sponsor)) END as cl
        WITH distinct ActivityName,aic,asgrp,aitmc1,ai,unit_ct,ct2,role,dtype,cl,
        CASE WHEN aitmc1.name='concept_id' THEN ct2.concept_id ELSE 
        CASE WHEN aitmc1.name='test_name_code' THEN ct2.concept_id END END as conceptId,
        CASE WHEN aitmc1.name='domain' THEN ct2.code_submission_value END as domain
        with distinct ActivityName,aic,asgrp,aitmc1,ai,unit_ct,ct2,role,dtype,conceptId,domain,
        CASE when (apoc.any.property(aic,'name')='NumericFinding') THEN 'Quantitative' ELSE 
        CASE WHEN (apoc.any.property(aic,'name')='CategoricFinding') THEN 'Ordinal' ELSE 
        null END END as aiclass
        WITH  conceptId, ActivityName, aiclass, asgrp.name as asgrp,  domain,  ai.name as conceptChildNames,  ai.adam_param_code as conceptChildIds, aitmc1,unit_ct,ct2,role,dtype,
        collect(distinct(coalesce(ct2.code_submission_value,unit_ct.name))) as val_lst
        WITH conceptId, ActivityName,conceptChildNames, conceptChildIds, aiclass, asgrp,domain,aitmc1,dtype.preferred_term as dtype,apoc.coll.flatten(collect(val_lst)) as val_list,toInteger(aitmc1.order) as var_order
        with conceptId, ActivityName,conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order
        call apoc.load.json('https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/C82590?include=minimal%2CinverseAssociations') yield value
        with distinct conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,value['inverseAssociations'] as class_concepts
        with conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,class_concepts,
      {PERCENTAGE:"Unit of Fraction",
      `RESPIRATORY RATE`:"Unit Respiratory Rate",
       CONCENTRATION:"Unit of Concentration",
      `U_IU Concentration`:"Unit of Concentration",
       TEMPERATURE:"Unit of Temperature",
       WEIGHT:"Unit of Weight",
       PRESSURE:"Unit of Pressure",
       FLOW:"Unit of Flow Rate",
      `VOLUMETRIC FLOW RATE`:"Unit of Volumetric Flow Rate",
      `CELL COUNT`:"Unit of Cell Count",
       LENGTH:"Unit of Length",
      `NO UNIT`:"No Unit",
       TIME:"Unit of Time",
      `BEAT RATE`:"Unit of Beat Rate"} as unit_dimension_dict
      WITH conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,class_concepts,unit_dimension_dict,
        CASE WHEN aitmc1.name='standard_unit' THEN 'Standard Result Unit' ELSE 
        CASE WHEN aitmc1.name='unit_dimension' THEN unit_dimension_dict[apoc.text.join(val_list,'')] ELSE
        CASE WHEN aitmc1.name='test_name_code' THEN "Test Code" ELSE 
        CASE WHEN aitmc1.name contains 'category' THEN 'Category' ELSE
        CASE WHEN aitmc1.name='domain' THEN 'Submission Domain' ELSE
        CASE WHEN aitmc1.name='specimen' THEN 'Biospecimen Type' ELSE
        apoc.text.join([c in class_concepts WHERE toUpper(c.relatedName)=toUpper(aitmc1.name) | c.relatedName],'') 
        END END END END END END as aitmc1_term
        WITH conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,apoc.text.replace(aitmc1_term," ","%20") as aitmc1_term
        call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/search?fromRecord=0&include=minimal&pageSize=10&term="+aitmc1_term+"&type=match&value=term") YIELD value
        WITH conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order, value.concepts[0].code as item_concept_id,aitmc1_term
        WITH conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,item_concept_id,aitmc1_term
        call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/search?fromRecord=0&include=minimal&pageSize=10&term="+aitmc1_term+"&type=startsWith&value=term") YIELD value
        WITH conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order, item_concept_id, apoc.text.join([v in value.concepts | v.code],',') as alt_item_concept_id
        WITH conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,
        CASE WHEN item_concept_id is null and not alt_item_concept_id is null THEN alt_item_concept_id ELSE  item_concept_id END as item_concept_id
        WITH conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,item_concept_id,
        CASE WHEN item_concept_id='' THEN '' ELSE 'https://ncithesaurus.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&ns=ncit&code='+item_concept_id END as href
        WITH distinct conceptId,ActivityName, conceptChildNames , conceptChildIds, aiclass, asgrp,  domain, aitmc1.name as aitmc1Name, apoc.text.join(collect(distinct dtype),',') as dtypes,apoc.coll.flatten(collect(val_list)) as val_list ,var_order,href,item_concept_id
       with distinct conceptId,ActivityName, conceptChildNames , conceptChildIds, aiclass, asgrp,domain,dtypes,aitmc1Name,val_list,var_order,href,item_concept_id
with distinct collect(conceptId) as conceptId, ActivityName, conceptChildNames , conceptChildIds, aiclass, asgrp, collect(domain) as domain, collect(apoc.map.fromPairs([['dtypes',dtypes],['aitmc1Name',aitmc1Name],['val_list',val_list],['var_order',var_order],['href',href],['item_concept_id',item_concept_id]])) as var_map
with conceptId, 
ActivityName, 
apoc.coll.toSet(collect(conceptChildNames)) as conceptChildNames, 
apoc.coll.toSet(collect(conceptChildIds)) as conceptChildIds , 
apoc.coll.toSet(collect(aiclass)) as aiclass, 
apoc.coll.toSet(collect(asgrp)) as asgrp, 
apoc.coll.toSet(domain) as domain,
apoc.coll.toSet(apoc.coll.flatten(collect(var_map))) as var_maps
with conceptId, ActivityName, conceptChildNames,conceptChildIds,aiclass,asgrp, domain, var_maps
UNWIND var_maps as var_map
with conceptId, ActivityName, conceptChildNames,conceptChildIds,aiclass,asgrp,domain,
var_map['dtypes'] as dtypes,
var_map['aitmc1Name'] as aitmc1Name,
var_map['val_list'] as val_list,
var_map['var_order'] as var_order,
var_map['href'] as href,
var_map['item_concept_id'] as item_concept_id
WITH conceptId, ActivityName, conceptChildNames,conceptChildIds,aiclass,asgrp,domain,apoc.coll.toSet(collect(dtypes)) as dtypes,aitmc1Name,apoc.coll.toSet(collect(href)) as href,apoc.coll.toSet(collect(item_concept_id)) as item_concept_id, apoc.coll.toSet(apoc.coll.flatten(collect(val_list))) as val_list, var_order
WITH conceptId, ActivityName, conceptChildNames,conceptChildIds,aiclass,asgrp,domain,
collect(apoc.map.fromPairs( [
                            ['conceptId', apoc.text.join(item_concept_id,',')],
                            ['href', apoc.text.join(href,',')],
                            ['shortName', aitmc1Name],
                            ['dataType',dtypes],
                            ['exampleSet',val_list],
                            ['var_order',var_order]
                            ])) as vars 
WITH conceptId, ActivityName,conceptChildNames,conceptChildIds,aiclass,asgrp,domain, vars where size(conceptId)<2
with apoc.text.join(conceptId,',') as conceptId, 
ActivityName,
apoc.text.join(conceptChildNames,';') as conceptChildNames,
apoc.text.join(conceptChildIds,';') as conceptChildIds,
apoc.text.join(aiclass,';') as aiclass, 
apoc.text.join(asgrp,';') as asgrp,
apoc.text.join(domain,';') as domain, 
vars
WITH CASE when conceptId = "" THEN 'C17998' ELSE conceptId END as conceptId,ActivityName, conceptChildNames,conceptChildIds,aiclass, asgrp,domain,vars
call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+conceptId+"?limit=100&include=minimal") YIELD value
WITH conceptId, ActivityName,conceptChildNames,conceptChildIds, aiclass,asgrp,domain, vars, value.name as conceptName
call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+conceptId+"/parents") YIELD value
WITH conceptId, ActivityName, conceptChildNames,conceptChildIds, aiclass,asgrp,domain, vars, conceptName,value.code as parentConceptId
CALL apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+conceptId+"?include=definitions") YIELD value 
WITH conceptId, ActivityName,conceptChildNames,conceptChildIds, aiclass,asgrp,domain, vars,conceptName, parentConceptId, value, [def IN value.definitions where def.source="NCI"] as def 
WITH conceptId, ActivityName,conceptChildNames,conceptChildIds, aiclass,asgrp,domain, vars,conceptName, parentConceptId, def[0]["definition"] as conceptDefinition
WITH conceptId, ActivityName,conceptChildNames,conceptChildIds, aiclass,asgrp,domain, vars,conceptName, parentConceptId,conceptDefinition
call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+conceptId+"?include=synonyms") YIELD value 
WITH conceptId, ActivityName,conceptChildNames,conceptChildIds, aiclass,asgrp,domain, vars,conceptName,parentConceptId,conceptDefinition,value, apoc.coll.toSet([sym IN value.synonyms where sym.source="CDISC" and sym.termType="PT"| sym.name]) as conceptSynonyms
WITH conceptId, ActivityName,conceptChildNames,conceptChildIds, aiclass,asgrp,domain, apoc.coll.sortMaps(vars, '^var_order') as vars,conceptName,parentConceptId,conceptDefinition,conceptSynonyms
WITH conceptId, ActivityName,conceptChildNames,conceptChildIds, aiclass,asgrp,domain, vars,conceptName,parentConceptId,conceptDefinition,conceptSynonyms,
apoc.map.fromPairs([ 
                            ['packageDate','2023-04-30'],
                            ['packageType','bc'],
                            ['conceptId',conceptId],
                            ['href', 'https://ncithesaurus.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&ns=ncit&code='+conceptId],
                            ['parentConceptId',parentConceptId],
                            ['category',asgrp],
                            ['shortName',conceptName],
                            ['activityName',ActivityName],
                            ['conceptChildrenNames',conceptChildNames],
                            ['conceptChildrenIds',conceptChildIds],
                            ['synonym',conceptSynonyms],
                            ['resultScale',aiclass],
                            ['definition',conceptDefinition],
                            ['domain',domain],
                            ['dataElementConcepts', vars]
                            ]) as activity
        return distinct activity
        """
        
        activity = db.graph().run(bc_query).data()
        for ai in activity:
            print('Concept_id:' ,ai['activity']['conceptId'])
            dom = ai['activity']['domain'].lower()
            #if the conceptId were null it was set to UNKNOWN (C17998)
            if ai['activity']['conceptId']=='C17998':          
              bc_file_name = 'biomedical_concept_'+dom+'_'+ai['activity']['activityName']
              print('Filename: ',bc_file_name)
              bc = {}
              bc = {
                  'packageDate': package_date,
                  'packageType': ai['activity']['packageType'],
                  'conceptId': 'NA',
                  'ncitCode': 'NA',
                  'href': 'NA',
                  'parentConceptId': 'NA',
                  'conceptChildrenNames': ai['activity']['conceptChildrenNames'],
                  'conceptChildrenIds':ai['activity']['conceptChildrenIds'],
                  'categories': ai['activity']['category'],
                  'shortName': ai['activity']['activityName'],
                  'synonyms': ai['activity']['conceptChildrenNames'],
                  'resultScales': ai['activity']['resultScale'],
                  'definition': 'NA',
                  'dataElementConcepts': []
              }
              bc['dataElementConcepts'] = []
              if ai['activity']['dataElementConcepts'] is not None:
                  for var in ai['activity']['dataElementConcepts']:
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
              path = 'nn_converted_data/bc/'
              if bc_file_name is not None:
                  filename = path+bc_file_name+'.yaml'
              with open(filename, 'w') as file:
                  yaml.dump([bc], file,sort_keys=False)
            else:
              bc_file_name = 'biomedical_concept_'+dom+'_'+ai['activity']['conceptId']
              print('Filename: ',bc_file_name)
              bc = {}
              bc = {
                  'packageDate': package_date,
                  'packageType': ai['activity']['packageType'],
                  'conceptId': ai['activity']['conceptId'],
                  'ncitCode': ai['activity']['conceptId'],
                  'href': ai['activity']['href'],
                  'parentConceptId': ai['activity']['parentConceptId'],
                  'conceptChildrenNames': ai['activity']['conceptChildrenNames'],
                  'conceptChildrenIds':ai['activity']['conceptChildrenIds'],
                  'categories': ai['activity']['category'],
                  'shortName': ai['activity']['shortName'],
                  'synonyms': ai['activity']['synonym'],
                  'resultScales': ai['activity']['resultScale'],
                  'definition': ai['activity']['definition'],
                  'dataElementConcepts': []
              }
              bc['dataElementConcepts'] = []
              if ai['activity']['dataElementConcepts'] is not None:
                  for var in ai['activity']['dataElementConcepts']:
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
                          
              path = 'nn_converted_data/bc/'
              if bc_file_name is not None:
                  filename = path+bc_file_name+'.yaml'
              with open(filename, 'w') as file:
                  yaml.dump([bc], file,sort_keys=False)  
              
process_instances_nn_concept()


    
