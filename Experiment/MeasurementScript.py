# tested on python 3.6

from SPARQLWrapper import SPARQLWrapper, JSON, XML, N3, RDF
from time import  gmtime, strftime
import time
import urllib.request    #Extracting web pages
import ast


endpoint = "https://data.labs.pdok.nl/sparql" #targer dataset
endpoint_primary = "https://data.labs.pdok.nl/sparql" #primary dataset

#target data location
TargetGraph = "https://data.pdok.nl/cbs/2015/buurt/"
vocab = "https://data.pdok.nl/cbs/2015/vocab/"
root = "https://data.pdok.nl/cbs/2015"


#prefix + URI
qualityGraph = ["qmd", "https://data.labs.pdok.nl/quality/id/"]
qualitySchema= ["qms", "https://data.labs.pdok.nl/quality/def#"]

#smoothing bypassess division by 0 error.
smoothing = 0.0001

#fetches current data (based on local time)
date_now = strftime("%Y-%m-%d", gmtime())
assessor = input("Please enter Assessor ID: ")

# read endpoint and open files to which triples are written.
sparql= SPARQLWrapper(endpoint)
f= open('Measurement.txt', 'w+')
f2= open('annotations.txt', 'w+')

#variable used in naming of measurements.
measurement = 0


#precomputed for testing purposes.
AoP=52
AoC=1
AoT=626261
AoR=12339

def make_measurement(result, metric, computedOn, datatype, date, assessor, note=""):
    global measurement
    measurement+=1
    triple_header = """#
# %smeasurement%d\n
%s:measurement%d a owl:NamedIndividual, dqv:QualityMeasurement ;
    dqv:isMeasurementOf %s:%s ;
    """%(qualityGraph[1], measurement, qualityGraph[0], measurement, qualityGraph[0], metric)
    triple_body="""dqv:computedOn <%s> ;
    dqv:value %s^^%s ;
    prov:generatedAtTime "%s"^^xsd:date ;
    prov:wasGeneratedBy "%s"@en ;
    skos:note "%s"@en .\n"""%(computedOn, result, datatype, date, assessor, note)
#     triples = """#\n# %smeasurement%d \n\n%s:measurement%d a owl:NamedIndividual, dqv:QualityMeasurement ;
#     %s:isMeasurementOf %s:%s ;
#     dqv:computedOn <%s> ;
#     dqv:value %s^^%s ;
#     prov:generatedAtTime "%s"^^xsd:date ;
#     prov:wasGeneratedBy "%s"@en ;
#     skos:note "%s"@en .\n"""%(QualityGraph, measurement, prefix, measurement, prefix, prefix, metric, computedOn, result, datatype, date, assessor, note)
    f.write(triple_header+triple_body)

def annotate(subjects, metric):
    if len(subjects) == 0:
        return
    elif len(subjects) == 1 :
        triple = "%s:%s %s:flags <%s> .\n"%(qualityGraph[0], metric, qualitySchema[0], subjects[0])
    else:
        linenr=1
        
        for i in subjects : 
            if linenr == 1 : 
                    triple = "%s:%s %s:flags <%s> ,\n"%(qualityGraph[0], metric, qualitySchema[0], i)
                    linenr +=1
            elif i != subjects[-1]:
                triple += "\t<%s> ,\n "%i
            else : triple += "\t<%s> .\n\n"%i
    f2.write(triple)
    


def value_parser(value):
    return ('"' + str(value) + '"')

def amountOfTriples(triples=True):
    query = """
        SELECT (count(?s) as ?count)
        WHERE {
            graph <%s> {
            ?s ?p ?o 
            }
        }
    """%TargetGraph
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    for result in results["results"]["bindings"]:
            if (triples==True) :
                return make_measurement(value_parser(result["count"]["value"]), "amountoftriples", TargetGraph, "xsd:integer", date_now, assessor)
            else: 
                return result["count"]["value"]
                
def amountOfClasses(triples=True):
    query = """
        SELECT (count(DISTINCT ?o) as ?count)
        WHERE {
            graph <%s> {
            ?s a ?o 
            }
        }
    """%TargetGraph
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    for result in results["results"]["bindings"]:
        if (triples==True) :
            return make_measurement(value_parser(result["count"]["value"]), "amountofclasses", TargetGraph, "xsd:integer", date_now, assessor)
        else: 
            return result["count"]["value"]
                
def amountOfProperties(triples=True):
    query = """
        SELECT (count(DISTINCT ?p) as ?count)
        WHERE {
            graph <%s> {
            ?s ?p ?o 
            }
        }
    """%TargetGraph
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    for result in results["results"]["bindings"]:
        if (triples==True) :
            return make_measurement(value_parser(result["count"]["value"]), "amountofproperties", TargetGraph, "xsd:integer", date_now, assessor)
        else: 
            return result["count"]["value"]     
        
def amountOfResources(triples=True):
    query = """
        SELECT (count(DISTINCT ?s) as ?count)
        WHERE {
            graph <%s> {
            ?s ?p ?o 
            }filter(!strstarts(str(?s),"https://data.pdok.nl/cbs/.well-known/genid/"))
        }
    """%TargetGraph
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    for result in results["results"]["bindings"]:
        if (triples==True) :
            return make_measurement(value_parser(result["count"]["value"]), "amountofresources", TargetGraph, "xsd:integer", date_now, assessor)
        else: 
            return result["count"]["value"]  
                 
def scalability(triples=True) :
    query = '''
    SELECT * 
    WHERE {
      ?sub ?pred ?obj .
    } 
    LIMIT 10
    '''
    
    sparql.setQuery(query)
    
    #fire a single query
    start_single = time.time()
    sparql.query()
    end_single = time.time()
    time_single = end_single - start_single
    
    #fire ten identical queries
    start_ten=time.time()
    for i in range(10):
        sparql.query()
    end_ten=time.time()
    time_ten = end_ten - start_ten
#     print((time_ten/10), time_single)
    if ( (time_ten/10) <= (time_single)) : 
        value='true'
    else:
        value='false'
    
    if (triples==True) :
        return make_measurement(value_parser(value), "scalability", TargetGraph, "xsd:boolean", date_now, assessor)
    else: 
        return value  
        
def schemaEnrichtment(triples=True):    
    annotate_list = []
    query = """
    Select DISTINCT ?property ?class
    
    WHERE {
      graph <%s> {
      {
        ?s ?property ?o .
        filter (!strstarts(str(?property), "%s"))
      }
      UNION{
        ?s2 a ?class . 
        filter (!strstarts(str(?class), "%s")) 
        }
      }
    }
    """ %(TargetGraph, vocab, vocab)
    sparql.setQuery(query)    
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    count=len(results["results"]["bindings"])
#     print(results["results"]["bindings"][0]['property']['value'])
    for result in results["results"]["bindings"] :
        try: 
            annotate_list.append(result['property']['value'])
        except :
            annotate_list.append(result['class']['value'])
    annotate(annotate_list, 'schemaenrichment')
#     p_count=0
#     c_count=0
#     for result in results["results"]["bindings"]:
# #         print(result)
#         for key in result:
# #             if key =='s':
# #                 print("write")
# #                 f.write((result[key]['value'] + " ex:hasFlag " "ex:schemaenrichment .\n"))
# #             print(key +": " +  result[key]["value"])
#             if key == 'property':
#                 p_count+= 1
#             else :
#                 c_count+=1
            
#     print("p_count: " + str(p_count) + " c_count: " + str(c_count))
    value = round((count / int(AoC + AoP)), 2)
    if (triples==True) :
        return make_measurement(value_parser(value), "schemaenrichment", TargetGraph, "xsd:float", date_now, assessor)
    else: 
        return value     

def malformedtriples(triples=True): 
    query='''
    SELECT * WHERE {
      GRAPH <%s> { {
          ?s ?p ?o .
          ?s2 a ?p .
        }
        UNION {
            ?s a ?o .
            ?s2 ?o ?o2 .
        }
      }
    }
    '''%TargetGraph
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    count=len(results["results"]["bindings"])
#         for key in result :
#             print('bla')
    if (triples==True) :
        return make_measurement(value_parser(count), "malformedtriples", TargetGraph, "xsd:integer", date_now, assessor)
    else: 
        return count        
          
def propertytype(triples=True):
    query="""PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT *
   WHERE {
       graph <%s> {
       {
           ?s ?p ?o .
           ?p a owl:DatatypeProperty .
#           filter (datatype(?o) = xsd:anyURI)
        }
        UNION {
            ?s ?p ?o .
            ?p a owl:ObjectProperty .
#           filter (datatype(?o) != xsd:anyURI)
               
  }}}"""%TargetGraph
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    count=len(results["results"]["bindings"])
    if (triples==True) :
        return make_measurement(value_parser(count), "propertytype", TargetGraph, "xsd:integer", date_now, assessor)
    else: 
        return count        
def propertyconsistency(triples=True):
    query="""
    SELECT DISTINCT ?s WHERE {
    graph <%s> {
        ?s ?p ?o ;
           ?p2 ?o2 .
        FILTER (?o = ?o2)
        } }"""%TargetGraph
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    count= len(results["results"]["bindings"])
    if (triples==True) :
        return make_measurement(value_parser(count), "propertyconsistency", TargetGraph, "xsd:integer", date_now, assessor)
    else: 
        return count   
def ontologyhijacking(triples=True):
    query='''
    SELECT * WHERE {
    graph <%s> {
    ?s ?p "50000009"^^xsd:integer .
    
#     FILTER (STRSTARTS(STR(?s), "nmhlkhkjh"))
        }
    }limit 10
    '''%(TargetGraph)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
#     return results
    if results["results"]["bindings"] == []:
        value='false'
    else :
        value='true'
    if (triples==True) :
        return make_measurement(value_parser(value), "ontologyhijacking", TargetGraph, "xsd:boolean", date_now, assessor)
    else: 
        return value   
#     for result in results["results"]["bindings"]:

def disjointClasses(triples=True):
    query=''' 
    SELECT * 
    WHERE {
    graph <%s> {{
        ?s a ?class1, ?class2 .
        ?class1 owl:disjointWith ?class2 .}
    UNION {
        ?s a ?class1,?class2 .
        ?class2 owl:disjointWith ?class1 .
    }
    }}
    
    '''%TargetGraph
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
#     return results
    value = len(results["results"]["bindings"])
    if (triples==True) :
        return make_measurement(value_parser(value), "disjointclasses", endpoint, "xsd:integer", date_now, assessor)
    else: 
        return value   
    
def malformeddatatypeliterals(triples=True):
    query='''
    SELECT *
    WHERE {
      GRAPH <%s> {
        SELECT ?malformed ?Literal_count WHERE {
            {
            SELECT (count(?o) as ?malformed ) WHERE {
                ?s ?p ?o .    
                FILTER (datatype(?o) = '')
                }
            }
            UNION {
                SELECT  (count(?o) as ?Literal_count) WHERE {
                    ?s?p?o .    
                    FILTER (!isURI(?o))
                }
            }
            }
        }
    }
    '''%TargetGraph
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    for result in results["results"]["bindings"]:
        for key in result:
            if key == 'malformed':
                malformed = float(result[key]['value'])+smoothing
            else: 
                literal_count = result[key]['value']
    value = round(float(malformed)/float(literal_count), 2)

    if (triples==True) :
        return make_measurement(value_parser(value), "malformeddatatypeliterals", TargetGraph, "xsd:float", date_now, assessor)
    else : return value
    
def SPARQLendpoint(triples=True):
    query='''
    SELECT * WHERE {
    ?s ?p ?o .
    }LIMIT 1 '''
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    note = input("<OPTIONAL> Add skos:note for SPARQLendpoint: ")
    value = 'true'
    try: 
        sparql.query().convert()
    except: 
        value = 'false'
    if (triples==True) :
        return make_measurement(value_parser(value), "SPARQLendpoint", endpoint, "xsd:boolean", date_now, assessor, note)
    else :
        return value
     
def dereferencability(samplesize,  triples=True):
    headers = {}
    headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
    
    query='''
    SELECT DISTINCT ?s WHERE {
    graph<%s> {
    ?s ?p ?o .
    }}LIMIT %d '''%(TargetGraph, samplesize)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    fail=0
    for result in results["results"]["bindings"]:
        try:
            req = urllib.request.Request(result['s']['value'], headers = headers)
            resp = urllib.request.urlopen(req)
        except :
            fail+=1
        time.sleep(1) # server friendly crawl
    value = round((1- fail/samplesize),2)
    note = "measured with a samplesize of %d"%samplesize
    if triples==True:
        return make_measurement(value_parser(value), "de-referencability",TargetGraph, "xsd:float", date_now, assessor, note)
    else : return value 
#         print (result['s']['value'])

# SPARQLendpoint(endpoint)
# RDFdump(TargetGraph)

def machinereadablelicence(triples=True):
    query='''PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT ?s ?o 
WHERE { graph <%s> {
?s a dcat:Dataset ;
   dcterms:licence ?o . 
}}'''%TargetGraph
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if results["results"]["bindings"] == []:
        value = 'false'        
    else : value = 'true'
    note = ""
    if value =='true':
        note = results["results"]["bindings"][0]['o']['value']
    
    return make_measurement(value_parser(value), "machine-readablelicence",TargetGraph, "xsd:boolean", date_now, assessor, note)
    
def indicativeness(triples=True):
    #count number of function in this script
    with open('metrics.py') as f2:
        tree = ast.parse(f2.read())
        max_measurement = (sum(isinstance(exp, ast.FunctionDef) for exp in tree.body))-3 # -3, for three functions in this file are not metrics.
    computedOn = qualityGraph[1] +"QualityMeasurementGraph"
    note = "%d of the %d metrics were measured"%(measurement+1, max_measurement)
    grade= round(((((measurement+1)/max_measurement)*9)+1),2)
    if triples==True:
        return make_measurement(value_parser(grade), "indicativeness",computedOn, "xsd:float", date_now, assessor, note)
    else : return grade
    
def blanknodes(triples=True):
    #isBlank seems to not work
#     query='''
#     SELECT (count(?bnode) as ?count) WHERE {
#     graph <%s> {
#     ?bnode ?p ?o
#     filter(isBlank(?bnode))}}
#     '''%TargetGraph
#     
    query='''
    SELECT (count(distinct ?s) as ?count) WHERE {
    graph <%s> {
    ?s ?p ?o
    filter(!strstarts(str(?s), "%s"))
    }
    }
    '''%(TargetGraph, root)
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    bnodes = results["results"]["bindings"][0]['count']['value']
    value = round((int(bnodes)/int(AoR)), 2)
    if triples==True:
        return make_measurement(value_parser(value), "blanknodes",TargetGraph, "xsd:float", date_now, assessor)
    else : return value
    
def prolixRDFFeatures(triples=True):
    query='''
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?p ?o2 WHERE {
graph <%s> {{
    ?s ?p ?o .
    filter(?p = rdfs:member ||?p = rdf:_n || ?p = rdf:subject || ?p= rdf:predicate || ?p=rdf:object)}
    UNION {
    ?s2 a ?o2 . 
    filter(?o =rdf:List || ?o= rdf:Statement || ?o=rdf:Alt || ?o=rdf:Bag || ?o=rdf:Seq || ?o=rdfs:Container || ?o=rdf:first || ?o=rdf:rest)
    }}}
    '''%TargetGraph
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if not results["results"]["bindings"] == []:
        value = results["results"]["bindings"][0]['p']['value'] + ["results"]["bindings"][1]['o2']['value']
    else : value = 0
    
    if triples==True:
        return make_measurement(value_parser(value), "prolixRDFfeatures",TargetGraph, "xsd:float", date_now, assessor)
    else : return value    

def coverage(triples=True):
    value = AoT / AoR
    note = "Scope = %d, descriptiveness = %d"%(AoR, value)
    if triples==True :
        make_measurement(value_parser(round(value,2)), "descriptiveness",TargetGraph, "xsd:float", date_now, assessor, note)
        return make_measurement(value_parser(AoR), "scope",TargetGraph, "xsd:integer", date_now, assessor, note)
    else : return (AoR, value) 
    
def interlinkingcompleteness(triples=True):
    query='''
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT ?s WHERE { GRAPH  <%s> {
    ?s owl:sameAs ?o .
    }}'''%TargetGraph
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    count=len(results["results"]["bindings"])
    if  count == 0 :
        count = smoothing
    value = round((smoothing / AoR),2)
    if triples==True :
        return make_measurement(value_parser(value), "interlinkingcompleteness",TargetGraph, "xsd:float", date_now, assessor)
    else : return (value) 
    
def deprecatedclasses(triples=True):
    query='''
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT (COUNT (?o) as ?count) WHERE { GRAPH <%s> {
    ?s ?p ?o . 
    ?o a owl:DeprecatedClass . 
    }}'''%TargetGraph
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if not results["results"]["bindings"] == []:
        value = results["results"]["bindings"][0]['count']['value']
    else: value=0
    if triples==True :
        return make_measurement(value_parser(value), "deprecatedclasses",TargetGraph, "xsd:integer", date_now, assessor)
    else : return (value) 

def deprecatedproperties(triples=True): 
    query='''
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT (COUNT (?p) as ?count) WHERE { GRAPH <%s> {
    ?s ?p ?o . 
    ?p a owl:DeprecatedProperty . 
    }}'''%TargetGraph
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert() 
    if not results["results"]["bindings"] == []:
        value = results["results"]["bindings"][0]['count']['value']
    else: value = 0
    if triples==True :
        return make_measurement(value_parser(value), "deprecatedproperties",TargetGraph, "xsd:integer", date_now, assessor)
    else : return (value)
    
    
## requires user input

  
def RDFdump(triples=True):
    print("\ninput constraints, please select from the following: true/false\n")
    value = input("<REQUIRED> Is there an RDFfdump available?")

    if not ((value == 'true') or (value == 'false')): 
        print("\nNo valid input, please retry.\n")
        return RDFdump(TargetGraph)
    note = input("<OPTIONAL> Add skos:note for RDFdump: ")
    if triples==True:
        return make_measurement(value_parser(value), "RDFdumpavailability",TargetGraph, "xsd:boolean", date_now, assessor, note)
    else : return value
  
def community(triples=True):
    print("\ninput constraints, please select from the following: true/false\n")
    value = input("<REQUIRED> Is there a Forum or mailing list (or something of the sort) for the given dataset available available? ")
    if not ((value == 'true') or (value == 'false')): 
        print("\nNo valid input, please retry.\n")
        return community()
    note = input("<OPTIONAL> Add skos:note for community: ")
    if triples==True:
        return make_measurement(value_parser(value), "community",TargetGraph, "xsd:boolean", date_now, assessor, note)
    else : return value 

def populationcompleteness(triples=True):
    print("\ninput constraints, please enter an integer or 'unknown'.\n")
    amount = input("<REQUIRED> What is the estimated number of real world objects in the scope of the dataset? ")
    if amount == 'unknown':
        return
    else:
        try:
            amount = int(amount)
        except :
            print("\nNo valid input, please retry.\n")
            return populationcompleteness()
        value = round((AoR / amount),2) 
        note= 'Population = %d, estimated real-world objects: %s. '%(AoR, amount)
        note= note + input("<OPTIONAL> Add skos:note for populationcompleteness: ")
        if triples==True:  
            return make_measurement(value_parser(value), "populationcompleteness",TargetGraph, "xsd:float", date_now, assessor, note)
        else : return value 
    
    
    
### CBS specific metrics

# def buurtGeometry(triples=True):
#     query='''
#     SELECT ?s WHERE { GRAPH <%s> {
#     ?s a <https://data.pdok.nl/cbs/2015/vocab/Buurt> .
#     ?s <http://www.opengis.net/ont/geosparql#hasGeometry> ?o .
#     filter((NOT ?o <http://www.opengis.net/ont/geosparql#asWKT> ?o2) || datatype(o2) !=<http://www.opengis.net/ont/geosparql#wktLiteral>)}}
#     
#     '''
    
def GeometryBlankNode(triples=True):
    query='''
SELECT (count(?s)as ?count) (count(?s2) as  ?count2) WHERE { GRAPH <%s>  {{
    ?s <http://www.opengis.net/ont/geosparql#hasGeometry> ?o . 
    filter(!strstarts(str(?o),"https://data.pdok.nl/cbs/.well-known/genid/"))}
    UNION{ 
    ?s2 <http://www.opengis.net/ont/geosparql#hasGeometry> ?o2 . } } }
    '''%TargetGraph
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    result= int(results["results"]["bindings"][0]['count']['value'])
    count= int(results["results"]["bindings"][0]['count2']['value'])
    value = (count - result) / count
    note= "Value depicts percentage of resources with a hasGeometry property, where the respective object is a blank node."
    if triples==True:  
        return make_measurement(value_parser(value), "geometryblanknode", TargetGraph, "xsd:float", date_now, assessor, note)
    else : return value 

def uniformspatialrepresentation(triples=True):
    query='''
PREFIX geosparql: <http://www.opengis.net/ont/geosparql#>

SELECT (count(?s1) as?geometry)(count( ?o)as?wkt) (count(?o2)as?gml) 
WHERE { GRAPH <%s> { {
    ?s1 <http://www.opengis.net/ont/geosparql#hasGeometry> ?o1.  }
    UNION { ?s ?p ?o . 
      filter( datatype(?o) = geosparql:wktLiteral) }
    UNION{ ?s2 ?p2 ?o2 . 
      filter( datatype(?o2) = geosparql:gmlLiteral) } } }
    '''%TargetGraph
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    geometry= int(results["results"]["bindings"][0]['geometry']['value'])
    wkt= int(results["results"]["bindings"][0]['wkt']['value'])
    gml= int(results["results"]["bindings"][0]['gml']['value'])
    if wkt == geometry and gml == 0 :
        value = 'true'
    elif gml == geometry and wkt == 0 :
        value = 'true'
    else : value = 'false'

    if triples==True:  
        return make_measurement(value_parser(value), "uniformspatialrepresentation", TargetGraph, "xsd:boolean", date_now, assessor)
    else : return value 
    
    
def surfacearea(triples=True):
    annotate_list = []
    query='''
Select ?s where { graph <%s> {{
    ?s <http://www.opengis.net/ont/geosparql#hasGeometry> ?o . 
    filter NOT EXISTS {
        ?s <https://data.pdok.nl/cbs/2015/vocab/oppervlakte> ?o2 . }}   
    }
}
    '''%TargetGraph
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    value = 1 - round((len(results["results"]["bindings"])/AoR),2)
    for result in results["results"]["bindings"]:
        annotate_list.append(result['s']['value'])
    annotate(annotate_list, 'surfacearea')
    if triples==True :
        return make_measurement(value_parser(value), "surfacearea", TargetGraph, "xsd:float", date_now, assessor)
    else : return value 
    

#execute things here

         
# AoT = amountOfTriples(TargetGraph, False)
# AoC = amountOfClasses(TargetGraph, False)
# AoP = amountOfProperties(TargetGraph, False)
# AoR = amountOfResources(TargetGraph, False)
#resultformats:
#uptime over time.
 
malformedtriples()
amountOfTriples()
amountOfClasses()
amountOfProperties()
amountOfResources()
scalability()
propertytype()
# propertyconsistency() #fails for this particular graph
ontologyhijacking()
disjointClasses()
malformeddatatypeliterals()
schemaEnrichtment()
dereferencability(1)
machinereadablelicence()
blanknodes()
prolixRDFFeatures()
deprecatedclasses()
deprecatedproperties()
interlinkingcompleteness()
coverage()
community()
RDFdump()
populationcompleteness()
       
GeometryBlankNode()
uniformspatialrepresentation()
surfacearea()
# 
indicativeness()  

# t1= time.time()
# amountOfResources()
# t2= time.time()
# print(t2-t1)

f.close()