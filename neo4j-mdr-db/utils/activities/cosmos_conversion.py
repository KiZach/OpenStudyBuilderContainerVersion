from neo4j_database import Neo4jDatabase
db = Neo4jDatabase()

def convert_to_cosmos_bc_concept(activity:str):
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
    OPTIONAL MATCH (p_unitdef:UnitDefinitionValue)-[R28:HAS_CT_DIMENSION]-(unit_term:CTTermRoot)-[R29:HAS_ATTRIBUTES_ROOT]->(clattr2)-[R31:LATEST]->(unit_cld), (unit_term:CTTermRoot)-[R30:HAS_NAME_ROOT]->(clattr3)-[:LATEST]->(unit_cld2)
    OPTIONAL MATCH(p_aitmc1)-[R32:HAS_ROLE]->(p_role_r:CTTermRoot),(p_role_r)-[R33:HAS_NAME_ROOT]->(ctnr_role)-[R34:LATEST]->(p_role_val), (p_role_r)-[R35:HAS_ATTRIBUTES_ROOT]->(ctattr)-[R36:LATEST]->(p_role_attr_val)
    OPTIONAL MATCH(p_aitmc1)-[R37:HAS_DATA_TYPE]->(p_dtype_r),(p_dtype_r)-[R38:HAS_NAME_ROOT]->(ctnr_dtype)-[R39:LATEST]->(p_dtype_val), (p_dtype_r)-[R40:HAS_ATTRIBUTES_ROOT]->(ctattr_dtype)-[R41:LATEST]->(p_dtype_attr_val)
    with distinct p_act.name as ActivityName, p_aic as aic, p_asgrp as asgrp, p_aitmc1 as aitmc1,p_ai as ai,p_unitdef as unit_ct,
    CASE WHEN p_unitdefr is not null THEN p_unitdef ELSE CASE WHEN p_ct2cd is not null THEN apoc.map.merge(properties(p_ct2_cdisc),properties(p_ct2_sponsor)) END END as ct2,
    CASE WHEN p_role_r is not null THEN apoc.map.merge(properties(p_role_val),properties(p_role_attr_val)) END as role,
    CASE WHEN p_dtype_r is not null THEN apoc.map.merge(properties(p_dtype_val),properties(p_dtype_attr_val)) END as dtype,
    CASE WHEN p_unitdefr is not null THEN apoc.map.merge(properties(unit_cld),properties(unit_cld)) ELSE CASE WHEN p_ct2cd is not null THEN apoc.map.merge(properties(p_cl_cdisc),properties(p_cl_sponsor)) END END as cl
    WITH distinct ActivityName,aic,asgrp,aitmc1,ai,unit_ct,ct2,role,dtype,cl,
    CASE WHEN aitmc1.name='concept_id' THEN ct2.concept_id ELSE 
    CASE WHEN aitmc1.name='test_name_code' THEN ct2.concept_id END END as conceptId,
    CASE WHEN aitmc1.name='domain' THEN ct2.code_submission_value END as domain
    with distinct ActivityName,aic,asgrp,aitmc1,ai,unit_ct,ct2,role,dtype,conceptId,domain,cl,
    CASE when (apoc.any.property(aic,'name')='NumericFinding') THEN 'Quantitative' ELSE 
    CASE WHEN (apoc.any.property(aic,'name')='CategoricFinding') THEN 'Ordinal' ELSE 'Nominal' END END  as aiclass
    WITH  conceptId, ActivityName, aiclass, asgrp.name as asgrp,  domain, aitmc1,unit_ct,ct2,role,dtype,cl,
    collect(distinct(coalesce(ct2.code_submission_value,unit_ct.name))) as val_lst
    WITH conceptId, ActivityName, aiclass, asgrp,domain,aitmc1,dtype.name_submission_value as dtype,apoc.coll.flatten(collect(val_lst)) as val_list,toInteger(aitmc1.order) as var_order,cl
    with conceptId, ActivityName, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,cl
    call apoc.load.json('https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/C82590?include=minimal%2CinverseAssociations') yield value
    with distinct conceptId, ActivityName, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,cl,value['inverseAssociations'] as class_concepts
    with conceptId, ActivityName, aiclass, asgrp,domain,dtype,cl,aitmc1,val_list,var_order,class_concepts,
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
    `BEAT RATE`:"Unit of Beat Rate"} as unit_dimension_dict,
    { DATETIME:'datetime', FLOAT:'decimal', INTEGER:'integer', CTTERM:'string', TEXT:'string'} as dtype_map
    WITH conceptId, ActivityName, aiclass, asgrp,domain,aitmc1,val_list,cl, var_order,class_concepts,unit_dimension_dict,dtype_map,
    CASE WHEN aitmc1.name='standard_unit' THEN apoc.text.join(['Unit of',cl.code_submission_value],' ') ELSE 
    CASE WHEN aitmc1.name='unit_dimension' THEN unit_dimension_dict[apoc.text.join(val_list,'')] ELSE
    CASE WHEN aitmc1.name='test_name_code' THEN "Test Code" ELSE 
    CASE WHEN aitmc1.name contains 'category' THEN 'Category' ELSE
    CASE WHEN aitmc1.name='domain' THEN 'Submission Domain' ELSE
    CASE WHEN aitmc1.name='specimen' THEN 'Biospecimen Type' ELSE
    apoc.text.join([c in class_concepts WHERE toUpper(c.relatedName)=toUpper(aitmc1.name) | c.relatedName],'') 
    END END END END END END as aitmc1_term, dtype_map[dtype] as dtype
    WITH conceptId, ActivityName,  aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,apoc.text.replace(aitmc1_term," ","%20") as aitmc1_term
    WITH conceptId, ActivityName,  aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,aitmc1_term
    call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/search?fromRecord=0&include=minimal&pageSize=10&term="+aitmc1_term+"&type=match&value=term") YIELD value
    WITH conceptId, ActivityName,  aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order, value.concepts[0].code as item_concept_id,aitmc1_term
    WITH conceptId, ActivityName,  aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,item_concept_id,aitmc1_term
    call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/search?fromRecord=0&include=minimal&pageSize=10&term="+aitmc1_term+"&type=startsWith&value=term") YIELD value
    WITH conceptId, ActivityName,  aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order, item_concept_id, apoc.text.join([v in value.concepts | v.code],',') as alt_item_concept_id
    WITH conceptId, ActivityName,  aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,
    CASE WHEN item_concept_id is null and not alt_item_concept_id is null THEN alt_item_concept_id ELSE  item_concept_id END as item_concept_id
    WITH conceptId, ActivityName,  aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,item_concept_id,
    CASE WHEN item_concept_id is null THEN null ELSE 'https://ncithesaurus.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&ns=ncit&code='+item_concept_id END as href
    WITH distinct conceptId,ActivityName, aiclass, asgrp,  domain, aitmc1.name as aitmc1Name, apoc.text.join(collect(distinct dtype),',') as dtypes,apoc.coll.flatten(collect(val_list)) as val_list ,var_order,href,item_concept_id
    with distinct conceptId,ActivityName,  aiclass, asgrp,domain,dtypes,aitmc1Name,val_list,var_order,href,item_concept_id
    with distinct collect(conceptId) as conceptId, ActivityName,  aiclass, asgrp, collect(domain) as domain, collect(apoc.map.fromPairs([['dtypes',dtypes],['aitmc1Name',aitmc1Name],['val_list',val_list],['var_order',var_order],['href',href],['item_concept_id',item_concept_id]])) as var_map
    with conceptId, 
    ActivityName, 
    apoc.coll.toSet(collect(aiclass)) as aiclass, 
    apoc.coll.toSet(collect(asgrp)) as asgrp, 
    apoc.coll.toSet(domain) as domain,
    apoc.coll.toSet(apoc.coll.flatten(collect(var_map))) as var_maps
    with conceptId, ActivityName, aiclass,asgrp, domain, var_maps
    UNWIND var_maps as var_map
    with conceptId, ActivityName, aiclass,asgrp,domain,
    var_map['dtypes'] as dtypes,
    var_map['aitmc1Name'] as aitmc1Name,
    var_map['val_list'] as val_list,
    var_map['var_order'] as var_order,
    var_map['href'] as href,
    var_map['item_concept_id'] as item_concept_id
    WITH conceptId, ActivityName, aiclass,asgrp,domain,dtypes,aitmc1Name,apoc.coll.toSet(collect(href)) as href,apoc.coll.toSet(collect(item_concept_id)) as item_concept_id, apoc.coll.toSet(apoc.coll.flatten(collect(val_list))) as val_list, var_order
    WITH conceptId, ActivityName, aiclass,asgrp,domain,dtypes,aitmc1Name, href,item_concept_id, val_list, var_order where not aitmc1Name in ['domain','test_name_code','unit_dimension']
    WITH conceptId, ActivityName, aiclass,asgrp,domain,dtypes,aitmc1Name, 
    CASE WHEN size(href)=0 THEN null ELSE  apoc.text.join(href,'') END as href,
    CASE WHEN size(item_concept_id)=0 THEN null ELSE apoc.text.join(item_concept_id,'') END as item_concept_id, 
    val_list, var_order 
    WITH conceptId, ActivityName, aiclass,asgrp,domain,
    collect(apoc.map.fromPairs( [
                                ['conceptId', item_concept_id],
                                ['href', href],
                                ['shortName', aitmc1Name],
                                ['dataType',dtypes],
                                ['exampleSet',val_list]
                                ])) as vars
    WITH conceptId, ActivityName,aiclass,asgrp,domain, vars where size(conceptId)<2
    with apoc.text.join(conceptId,',') as conceptId, 
    ActivityName,
    aiclass, 
    asgrp,
    apoc.text.join(domain,';') as domain, 
    vars
    WITH CASE when conceptId = "" THEN 'C17998' ELSE conceptId END as conceptId,ActivityName,aiclass, asgrp,domain,vars
    call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+conceptId+"?limit=100&include=minimal") YIELD value
    WITH conceptId, ActivityName, aiclass,asgrp,domain, vars, value.name as conceptName
    call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+conceptId+"/parents") YIELD value
    WITH conceptId, ActivityName, aiclass,asgrp,domain, vars, conceptName,collect(value.code)[0] as parentConceptId
    CALL apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+conceptId+"?include=definitions") YIELD value 
    WITH conceptId, ActivityName, aiclass,asgrp,domain, vars,conceptName, parentConceptId, value, [def IN value.definitions where def.source="NCI"] as def 
    WITH conceptId, ActivityName, aiclass,asgrp,domain, vars,conceptName, parentConceptId, def[0]["definition"] as conceptDefinition
    WITH conceptId, ActivityName, aiclass,asgrp,domain, vars,conceptName, parentConceptId,conceptDefinition
    call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+conceptId+"?include=synonyms") YIELD value 
    WITH conceptId, ActivityName, aiclass,asgrp,domain, vars,conceptName,parentConceptId,conceptDefinition,value, apoc.coll.toSet([sym IN value.synonyms where sym.source="CDISC" and sym.termType="PT"| sym.name]) as conceptSynonyms
    WITH conceptId, ActivityName, aiclass,asgrp,domain, apoc.coll.sortMaps(vars, '^var_order') as vars,conceptName,parentConceptId,conceptDefinition,conceptSynonyms
    WITH conceptId, ActivityName, aiclass,asgrp,domain, vars,conceptName,parentConceptId,conceptDefinition,conceptSynonyms,
    apoc.map.fromPairs([ 
                        ['packageDate','2023-04-30'],
                        ['packageType','bc'],
                        ['conceptId',conceptId],
                        ['href', 'https://ncithesaurus.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&ns=ncit&code='+conceptId],
                        ['parentConceptId',parentConceptId],
                        ['category',asgrp],
                        ['shortName',conceptName],
                        ['activityName',ActivityName],
                        ['synonym',conceptSynonyms],
                        ['resultScale',aiclass],
                        ['definition',conceptDefinition],
                        ['domain',domain],
                        ['dataElementConcepts', vars]
                        ]) as activity
                return distinct activity
    """
    cosmos_bc = db.graph().run(bc_query).data()   
    return cosmos_bc

def convert_to_cosmos_sdtm_specialization(activity:str, sdtm_version:str):
    sdtm_query ="""
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
                WITH distinct g,sg,p_agrp,p_asgrp,p_act,p_ai,p_aicr,p_aic,p_aitm1,p_aitmc1r,p_aitmc1,p_aicrp,p_aicp,p_aicrpp,p_aicpp,p_ct2cd,ct2cdr,p_ct2_sponsor,ct2att,p_ct2_cdisc,p_unitdefr,p_unitdef,clr,clatt,clattr,p_cl_sponsor,p_cl_cdisc,unit_term,cl_root,clattr2,unit_cld,p_role_r,ctattr,ctnr_role, p_role_val, p_role_attr_val,p_dtype_r,p_dtype_val, ctnr_dtype,p_dtype_attr_val,ctattr_dtype,R1,R2, R3, R4, R5, R6, R8, R9, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20, R21, R22, R23, R24, R25, R26, R27, R28, R29, R30, R31, R32, R33, R34, R35, R36, R37, R38, R39, R40, R41,R42,R43
                MATCH (p_ai:ActivityInstanceValue)-[:CONTAINS_ACTIVITY_ITEM]->(p_aitm1_dom:ActivityItem)<-[:HAS_ACTIVITY_ITEM]-(:ActivityItemClassRoot)-[:MAPS_VARIABLE_CLASS]->(:VariableClass{uid:'DOMAIN'})-[:HAS_INSTANCE]->(:VariableClassInstance)<-[:IMPLEMENTS_VARIABLE{version_number:'"""+sdtm_version+"""'}]-(:DatasetVariableInstance)<-[:HAS_DATASET_VARIABLE{version_number:'"""+sdtm_version+"""'}]-(:DatasetInstance)<-[:HAS_INSTANCE]-(p_ds:Dataset),(p_aitm1_dom:ActivityItem)-[x]->(y:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(p_ct2_sponsor_dom), (y)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(p_ct2_cdisc_dom)  where p_ds.uid=p_ct2_cdisc_dom.code_submission_value OPTIONAL MATCH(p_aitmc1r)-[R44:MAPS_VARIABLE_CLASS]->(p_varcl:VariableClass)-[R45:HAS_INSTANCE]->(p_varcli:VariableClassInstance)
                ,(p_varcli)<-[R46:IMPLEMENTS_VARIABLE{version_number:'"""+sdtm_version+"""'}]-(var:DatasetVariableInstance)<-[R47:HAS_DATASET_VARIABLE{version_number:'"""+sdtm_version+"""'}]-(p_dsi:DatasetInstance)<-[R48:HAS_INSTANCE]-(p_ds:Dataset)<-[R49:HAS_DATASET]-(p_dmcat:DataModelCatalogue)-[R50:CONTAINS_VERSION]->(p_dmig:DataModelVersion),(p_dsi)<-[R51:HAS_DATASET]-(p_dmigv:DataModelIGValue)<-[R52:CONTAINS_DATA_MODEL_IG]-(p_dmig),(p_dmcat)-[:HAS_DATASET_VARIABLE]->(dsv:DatasetVariable)-[:HAS_INSTANCE]->(var) where p_dmigv.version_number='"""+sdtm_version+"""' 
                optional match(p_dmigv)<-[:EXTENDS_VERSION]-(s_modl_val:SponsorModelValue)-[:HAS_DATASET]->(s_ds:SponsorModelDatasetInstance)<-[:HAS_INSTANCE]-(p_ds:Dataset)-[:HAS_INSTANCE]->(p_dsi)
                Optional match(s_ds)-[:HAS_DATASET_VARIABLE]->(s_sdv:SponsorModelDatasetVariableInstance)<-[:HAS_INSTANCE]-(dsv:DatasetVariable)-[:HAS_INSTANCE]->(p_dci)
                with p_aic,p_ai,p_aitmc1,p_dmigv,p_ds, p_varcl,dsv,var,p_role_val,p_dtype_val,clr,p_cl_cdisc,p_cl_sponsor,p_ct2cd,p_ct2_cdisc, p_ct2_sponsor, p_unitdef.name as unit_ct,
                split(split(p_unitdef.definition,'CDISC code: ')[1],'_x000D')[0] as unit_code, s_sdv where not p_aitmc1.name in ['unit_dimension','domain']
                with p_aic,p_ai,p_aitmc1,p_dmigv, p_ds, p_varcl,dsv,var,p_role_val,p_dtype_val,clr,p_cl_cdisc,p_cl_sponsor,p_ct2cd,p_ct2_cdisc, p_ct2_sponsor,unit_ct,s_sdv,
                CASE when p_ct2cd is not NULL THEN
                CASE WHEN var.role='Topic' THEN
                apoc.map.fromPairs([
                  ['code',p_ct2cd.concept_id],
                  ['submission_value',coalesce(p_ct2_cdisc.code_submission_value,toUpper(p_ct2_sponsor.name))],
                  ['shortName',p_ct2_cdisc.preferred_term]
                  ]) 
                  ELSE
                  CASE WHEN p_varcl.uid="--TEST" THEN
                  apoc.map.fromPairs([
                  ['code',p_ct2cd.concept_id],
                  ['submission_value',coalesce(p_ct2_cdisc.preferred_term,toUpper(p_ct2_sponsor.name))]
                  ]) 
                  ELSE
                  apoc.map.fromPairs([
                  ['code',p_ct2cd.concept_id],
                  ['submission_value',coalesce(p_ct2_cdisc.code_submission_value,toUpper(p_ct2_sponsor.name))]
                  ]) END
                  END ELSE
                  apoc.map.fromPairs([
                  ['code',unit_code],
                  ['submission_value',unit_ct]
                  ])
                  END as val_list
                  WITH p_aic,p_ai,p_aitmc1,p_dmigv, p_ds, p_varcl,dsv,var,p_role_val,p_dtype_val,clr,p_cl_cdisc,p_cl_sponsor,s_sdv,collect(distinct val_list) as terms, 
                  { DATETIME:'datetime', FLOAT:'float', INTEGER:'integer', CTTERM:'text', TEXT:'text'} as dtype_map
                  WITH p_aic,p_ai,p_aitmc1,p_dmigv, p_ds,p_varcl,dsv,s_sdv,var,p_role_val,[x IN ['Identifier', 'Qualifier', 'Timing', 'Topic'] WHERE var.role contains x][0] as role,p_dtype_val,dtype_map[toUpper(p_dtype_val.name)] as dtype,clr, p_cl_cdisc,p_cl_sponsor,terms,
                  CASE WHEN var.role='Topic' THEN apoc.text.join([p_ds.uid,dsv.uid],'.') END as source,
                      CASE WHEN clr is not NULL THEN
                apoc.map.fromPairs([['conceptId',clr.uid],
                                  ['href','https://ncithesaurus.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&ns=ncit&code='+clr.uid],                  ['submissionValue',coalesce(p_cl_cdisc.submission_value,toUpper(p_cl_sponsor.name))]
                                  ]) END as cdlist,
                CASE WHEN size(terms)=1 THEN
                apoc.map.fromPairs([
                                  ['conceptId',terms[0]['code']],
                                  ['value',terms[0]['submission_value']]
                                  ]) 
                END as assignedTerms,
                CASE WHEN size(terms)>1 THEN [ v in terms | v['submission_value']] END as valueList,
                CASE when p_aitmc1.data_collection='Yes' THEN 'Collected' ELSE 'Not Collected' END as collected
                WITH p_aic,p_ai, p_aitmc1,p_dmigv, p_ds,p_varcl,dsv,var,role,
                p_dtype_val,dtype, assignedTerms, valueList,cdlist,source,terms,s_sdv,
                CASE WHEN assignedTerms is not null THEN
                        CASE WHEN var.role='Topic' and dsv.uid=cdlist['submissionValue'] THEN
                          apoc.map.fromPairs( [
                                                ['name', dsv.uid],
                                                ['isNonStandard',false],
                                                ['role',role],
                                                ['dataType', dtype],
                                                ['codelist',cdlist],
                                                ['assignedTerm',assignedTerms],
                                                ['originType', s_sdv.origin],
                                                ['mandatoryVariable', p_aitmc1.mandatory],
                                                ['mandatoryValue', p_aitmc1.mandatory]
                                                ]) 
                        ELSE
                        CASE WHEN p_varcl.uid='--TEST' and dsv.uid=cdlist['submissionValue'] THEN
                            apoc.map.fromPairs( [
                                                ['name', dsv.uid],
                                                ['isNonStandard',false],
                                                ['role',role],
                                                ['dataType', dtype],
                                                ['codelist',cdlist],
                                                ['assignedTerm',assignedTerms],
                                                ['originType', s_sdv.origin],
                                                ['mandatoryVariable', p_aitmc1.mandatory],
                                                ['mandatoryValue', p_aitmc1.mandatory]
                                                ]) 
                        ELSE  
                            CASE WHEN not p_varcl.uid contains 'TEST'  THEN 
                              apoc.map.fromPairs( [
                                                ['name', dsv.uid],
                                                ['dataElementConceptId',p_aitmc1.nci_concept_id],
                                                ['isNonStandard',false],
                                                ['role',role],
                                                ['dataType', dtype],
                                                ['codelist',cdlist],
                                                ['assignedTerm',assignedTerms],
                                                ['originType', s_sdv.origin],
                                                ['mandatoryVariable', p_aitmc1.mandatory],
                                                ['mandatoryValue', p_aitmc1.mandatory]
                                                ]) END
                        END END
                    ELSE
                        CASE WHEN valueList is not null THEN 
                            apoc.map.fromPairs( [
                            ['name', dsv.uid],
                            ['dataElementConceptId',p_aitmc1.nci_concept_id],
                            ['isNonStandard',false],
                            ['codelist',cdlist],
                            ['valueList', valueList],
                            ['role',role],
                            ['originType', s_sdv.origin],
                            ['mandatoryVariable', p_aitmc1.mandatory],
                            ['mandatoryValue', p_aitmc1.mandatory]
                            ]) 
                        ELSE   
                            apoc.map.fromPairs( [
                            ['name', dsv.uid],
                            ['dataElementConceptId',p_aitmc1.nci_concept_id],
                            ['isNonStandard',false],
                            ['role',role],
                            ['dataType', dtype],
                            ['codelist',cdlist],
                            ['valueList', valueList],
                            ['originType', s_sdv.origin],
                            ['mandatoryVariable', p_aitmc1.mandatory],
                            ['mandatoryValue', p_aitmc1.mandatory]
                            ]) 
                END
                    END as dataElement,
                CASE WHEN var.role='Topic' THEN assignedTerms['conceptId'] END as biomedicalConceptId,
                p_ai.adam_param_code as datasetSpecializationId,
                CASE WHEN var.role='Topic' THEN [ v in terms | v['shortName']][0] END as shortName  
                WITH p_aic,p_ai,apoc.coll.toSet(collect(shortName))[0] as shortName,p_dmigv, p_ds,apoc.coll.toSet(collect(source))[0] as source,apoc.coll.toSet(collect(biomedicalConceptId))[0] as biomedicalConceptId, apoc.coll.toSet(collect(datasetSpecializationId))[0] as datasetSpecializationId , collect(distinct dataElement) as vars
                WITH p_aic,p_ai,shortName,p_dmigv, p_ds,source,datasetSpecializationId,biomedicalConceptId,vars, 
                apoc.map.fromPairs([ 
                                    ['packageType','sdtm'],
                                    ['datasetSpecializationId',datasetSpecializationId],
                                    ['domain',p_ds.uid],
                                    ['shortName',shortName],
                                    ['source',source],
                                    ['sdtmigStartVersion',p_dmigv.version_number],
                                    ['sdtmigEndVersion',""],
                                    ['biomedicalConceptId',biomedicalConceptId],
                                    ['variables',vars]
                                    ]) as activity
                return  activity
                """
    cosmos_sdtm_specialization = db.graph().run(sdtm_query).data()
    return cosmos_sdtm_specialization