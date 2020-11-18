import re
import json
from app.config import Config
from app.forms import MissingFieldReportForm, MissingSubfieldReportForm, SelectAuthority
#import dlx
from dlx import DB
from dlx.marc import Bib, Auth, BibSet, AuthSet, QueryDocument,Condition,Or
import pymongo
from pymongo import MongoClient, ReplaceOne
import time
from app.models import Itpp_itp, Itpp_section, Itpp_rule#, list_all_sections
from mongoengine import connect,disconnect



DB.connect(Config.connect_string)
connect(host=Config.connect_string,db=Config.dbname)
db_client=MongoClient(Config.connect_string)
db=db_client['undlFiles']
rules_coll = db['dev_Itpp_document']
snapshot_coll=db['itpp_snapshot_test3']
itp_bib_fields=[]


class Snapshot(object):
    def __init__(self,body, session):
        self.name = None
        self.title = None
        self.description = "New Snapshot"
        #self.form_class = SelectAuthority
        self.expected_params = "authority"
        self.body=body
        self.session=session
        #self.snapshot_len = None
        self.replace_list_recs=[]
        self.snapshots_list=[]


    def fields_to_extract(self):
        itp_bib_fields=[]
        #1. get the list of fields for the ITP
        itp_bib_fields=[]
        for itp in Itpp_itp.objects:
            print(itp.name)
        try:
            itpp_doc = Itpp_itp.objects.get(name=self.body+self.session,sections__rules__name="fields_needed")
        except:
            print(f" there is no matching ITP document")
            itpp_doc=None
        if itpp_doc is not None: 
            for itpp_section in itpp_doc.sections:
                #print(f"    {itpp_section.name}")
                for itpp_rule in itpp_section.rules:
                    #print(f"        {itpp_rule.name}")
                    if itpp_rule.name == "fields_needed":
                        #print(f"        {itpp_rule.parameters}")
                        for fld in itpp_rule.parameters[0].split(";"):
                            itp_bib_fields.append(fld.strip()) 
        else:
            itp_bib_fields=['001', '035$a', '591$a','700$a', '700$g', '710$a', '711$a', '791$a','791$b','791$c','793$a', '930$a', '949$a','991$b', '991$d','001', '035$a', '089$b', '191$9', '191$a', '191$b', '191$c','191$d', '191$z', '239$a', '245$a', '245$b', '245$c', '248$a', '249$a', '260$a','260$b','260$c','269$a','300$a', '495$a', '515$a', '520$a', '580$a', '591$a', '592$a', '598$a', '599$a', '791$b', '791$c', '930$a', '949$a', '991$a', '991$b', '991$c', '991$d', '991$e', '991$m', '991$s', '991$z', '992$a', '995$a', '996$a','967$c','967$d','968$c','968$d','969$c','969$d']
        itp_auth_fields=['191$a','191$b', '191$c','191$d']
        set_itp_bib_fields=sorted(set(itp_bib_fields))
        set_itp_auth_fields=sorted(set(itp_auth_fields))
        print(f"bib fields are: {set_itp_bib_fields}")   
        print(f"auth fields are: {set_itp_auth_fields}")      
        # 2. prepare a proper structure of tuples for easier processing e.g.
        # [[(035,a)], [(089,a)], [(191,9), (191,a),  (191,b),  (191,c)]]
       
        set_itp_bib_flds=set(map(lambda x:x.split("$")[0], set_itp_bib_fields))
        proj_bib_dict={}
        #same but for auth fields
        set_itp_auth_flds=set(map(lambda x:x.split("$")[0], set_itp_auth_fields))
        proj_auth_dict={}

        for k in set_itp_bib_flds:
            proj_bib_dict[k]=True

        #same but for auth fields
        for ka in set_itp_auth_flds:
            proj_auth_dict[ka]=True

        itpp_bib_fields=[]
        #same but for auth fields
        itpp_auth_fields=[]
        f=''
        for itp_bib_field in set_itp_bib_fields:
            if itp_bib_field !="001":
                if itp_bib_field.split("$")[0] !=f:
                    temp_f=[]
                    temp_f.append((itp_bib_field.split("$")[0],itp_bib_field.split("$")[1]))
                    itpp_bib_fields.append(temp_f)
                else:
                    temp_f.append((itp_bib_field.split("$")[0],itp_bib_field.split("$")[1]))
                f=itp_bib_field.split("$")[0]
                #s_f=itp_field.split("$")[1]
                #print(f"proj_dict: {proj_dict}") 
                #print(f"itpp_bib_fields: {itpp_bib_fields}")
        f=''
        for itp_auth_field in set_itp_auth_fields:
            if itp_auth_field !="001":
                if itp_auth_field.split("$")[0] !=f:
                    temp_auth_f=[]
                    temp_auth_f.append((itp_auth_field.split("$")[0],itp_auth_field.split("$")[1]))
                    itpp_auth_fields.append(temp_auth_f)
                else:
                    temp_auth_f.append((itp_auth_field.split("$")[0],itp_auth_field.split("$")[1]))
                f=itp_auth_field.split("$")[0]  
        return proj_bib_dict,itpp_bib_fields,proj_auth_dict,itpp_auth_fields


    def fetch_bib_data(self,proj_dict):
        query = QueryDocument(
            Or(
                Condition(
                tag='191',
                subfields={'b': self.body+'/','c':self.session}
                    ),
                Condition(
                tag='791',
                subfields={'b': self.body+'/','c':self.session}
                    ),
                Condition(
                tag='930',
                subfields={'a': 'ITP'+self.body+self.session}
                    )
                )
            )
        #print(query.to_json())
        bibset=BibSet.from_query(query, projection=proj_dict, skip=0, limit=0)
        #l_temp=bibset.count
        #self.snapshot_len=l_temp 
        lbibs=list(bibset.records)
        print(f"bibset length is : {len(lbibs)}")
        return lbibs#, l_temp


    def fetch_auth_data(self,proj_auth_dict):
        query_auth = QueryDocument(
                Condition(
                tag='191',
                subfields={'a': re.compile('^'+self.body+'/'+self.session[0:4])}
                    )
            )
        #print(query.to_json())
        authset=AuthSet.from_query(query_auth, projection=proj_auth_dict, skip=0, limit=0)
        lauths=list(authset.records)
        print(f"authset length is : {len(lauths)}")
        return lauths#, l_temp
        
   
    ''' get the subfield values'''
    def list_of_subfields(self,bib,fld,sbflds):
        temp_lst=[]
        
        for field in bib.get_fields(fld):
            temp_dict={}
            for sub in field.subfields:
                if sub.code in sbflds:
                    #temp_dict[sub.code]= sub.value
                    if len(bib.get_values(fld, sub.code))==1:
                        temp_dict[sub.code]= ''.join(bib.get_values(fld, sub.code))
                    else:
                        temp_dict[sub.code]= bib.get_values(fld, sub.code)
            temp_lst.append(temp_dict)
        return temp_lst

      
    ''' not used any more'''           
    def execute_bibs(self):
        proj_bib_dict,itpp_bib_fields=self.fields_to_extract()
        lbibs,l_temp=self.fetch_bib_data(proj_bib_dict)
        return lbibs,itpp_bib_fields



    '''transforming data to snapshot schema'''
    def process_bib_records(self,chunk_no,no_of_chunks,lbibs,itpp_bib_fields):
        chunk_size=len(lbibs)//(no_of_chunks-1)
        if chunk_no==(no_of_chunks-1):
            end_rec=len(lbibs)
        else:
            end_rec=(chunk_no)*chunk_size

        for bib in lbibs[(chunk_no-1)*chunk_size:end_rec]:
            #print(f"bib id is {bib.id}")
            bib_dict={}
            if "ITS" in bib.get_values('930','a'):
                bib_dict["record_type"]="ITS"
            elif "VOT" in bib.get_values('930','a'):
                bib_dict["record_type"]="VOT"
            else:
                bib_dict["record_type"]="BIB"

            bib_dict["record_id"]=bib.id
            bib_dict["bodysession"]=self.body+'/'+self.session
            bib_dict["snapshot_id"]=str(bib.id)+self.body+self.session
            named_tuple = time.localtime() # get struct_time
            time_string = time.strftime("%Y-%m-%d %H:%M:%S", named_tuple)
            bib_dict["snapshottime"]=time_string

            for itpp_field_subfields in itpp_bib_fields:
                sbflds=[]
                for elem in itpp_field_subfields:
                    field=elem[0]
                    sbflds.extend(elem[1])
                temp_dict={}
                temp_dict[field]=self.list_of_subfields(bib,field,sbflds)
                if len(temp_dict[field])>1:
                    bib_dict[field]=temp_dict[field]
                elif len(temp_dict[field])==1:
                    bib_dict[field]=temp_dict[field][0]
                else:
                    bib_dict[field]=""
            #snapshot_list_bibs.append(bib_dict)
            #query={"record_id":bib_dict["record_id"]}
            query={"snapshot_id":bib_dict["snapshot_id"]}
            self.replace_list_recs.append(ReplaceOne(query, bib_dict, upsert=True))
        return len(self.replace_list_recs)



    '''transforming data to snapshot schema for auths'''
    def process_auth_records(self,lauths,itpp_auth_fields):
        for auth in lauths:
            #print(f"bib id is {bib.id}")
            auth_dict={}
            auth_dict["record_type"]="AUTH"

            auth_dict["record_id"]=auth.id
            auth_dict["bodysession"]=self.body+'/'+self.session
            auth_dict["snapshot_id"]=str(auth.id)+self.body+self.session
            named_tuple = time.localtime() # get struct_time
            time_string = time.strftime("%Y-%m-%d %H:%M:%S", named_tuple)
            auth_dict["snapshottime"]=time_string

            for itpp_field_subfields in itpp_auth_fields:
                sbflds=[]
                for elem in itpp_field_subfields:
                    field=elem[0]
                    sbflds.extend(elem[1])
                temp_dict={}
                temp_dict[field]=self.list_of_subfields(auth,field,sbflds)
                if len(temp_dict[field])>1:
                    auth_dict[field]=temp_dict[field]
                elif len(temp_dict[field])==1:
                    auth_dict[field]=temp_dict[field][0]
                else:
                    auth_dict[field]=""
            #snapshot_list_bibs.append(bib_dict)
            #query={"record_id":bib_dict["record_id"]}
            query={"snapshot_id":auth_dict["snapshot_id"]}
            self.replace_list_recs.append(ReplaceOne(query, auth_dict, upsert=True))
        return len(self.replace_list_recs)






    ''' writing data into snapshot collection'''    
    def bulk_write_bibs_auths(self):
        try:
            print("No. of replace_list_bibs_auths records is: {}".format(len(self.replace_list_recs)))
            snapshot_coll.bulk_write(self.replace_list_recs)
        except:
            warning="something went wrong with insert into MDb"    
    '''asynch function'''
    def transform_write(self):
        proj_bib_dict,itpp_bib_fields,proj_auth_dict,itpp_auth_fields=self.fields_to_extract()
        #lbibs,l_temp=self.fetch_bib_data(proj_dict)
        lbibs=self.fetch_bib_data(proj_bib_dict)
        no_of_chunks=10
        for i in range(1,no_of_chunks+1):
            start_time_chunk=time.time()
            len1=self.process_bib_records(i,no_of_chunks+1,lbibs,itpp_bib_fields)
            print(f"--- {time.time() - start_time_chunk} seconds for chunk {i} run ---")
            print(f"chunk No is: {i}; records processed are {len1}")
            #print("No. of ITP its records is: {}".format(number_itss))
        print(f"No. of ITP records is: {len(self.replace_list_recs)}")
        
        lauths=self.fetch_auth_data(proj_auth_dict)
        start_time_auths=time.time()
        len_auths=self.process_auth_records(lauths,itpp_auth_fields)
        print(f"--- {time.time() - start_time_auths} seconds for auths run ---")
        #print(f"Auth records processed are {len(lauths)}")            #print("No. of ITP its records is: {}".format(number_itss))
        print(f"No. of ITP records is: {len(self.replace_list_recs)}")

        start_time_bulk_write=time.time()
        self.bulk_write_bibs_auths()
        print(f"--- {time.time() - start_time_bulk_write} seconds for bulk write for {self.body}/{self.session} ---")

    ''' listing snapshots in display snapshot'''
    def list(self):
        snapshots=snapshot_coll.distinct("bodysession")
        for sh in snapshots:
            #self.snapshots_list.append((sh,snapshot_coll.find_one({'bodysession':sh},sort=[( '_id', pymongo.DESCENDING )])['_id'].generation_time.strftime("%Y-%m-%d %H:%M:%S")))
            try:
                self.snapshots_list.append((sh, snapshot_coll.find_one({'bodysession':sh},sort=[('snapshottime', -1)])['snapshottime']))
            except:
                self.snapshots_list.append((sh,snapshot_coll.find_one({'bodysession':sh},sort=[( '_id', pymongo.DESCENDING )])['_id'].generation_time.strftime("%Y-%m-%d %H:%M:%S")))

        return sorted(self.snapshots_list,key=lambda x: x[1], reverse = True)
        #return sorted(self.snapshots_list, reverse = True)







