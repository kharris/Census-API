import bs4, fips, pathlib, pandas as pd, requests
from bs4 import BeautifulSoup as bsp
from datetime import datetime as dtm
from pathlib import Path

pd.set_option('max.columns',None)
null = None

NEEDS_FIPS = ['state','county']
geoHeirs = {"State" : ["State"],
        "County" : ["State","County"],
        "Tract" : ["State","County","Tract"],
        "Block%20Group" : ["State","County","Tract","Block Group"],
        "Congressional%20District" : ["State","Congressional District"]}

def getFipsDict(dictName,queryurl):
    refFile = Path(r".\fips.py")

    fipsdf = ConstructDF(queryurl)
    cols = list(fipsdf.columns)
    fipsDict = dict(zip(fipsdf[cols[0]],fipsdf[cols[-1]]))

    outString = dictName.upper() + ' = {'
    for n,vals in enumerate(fipsDict.items()):
        name = vals[0].split(',')[0].lower() if ',' in vals[0] else vals[0].lower()
        outString += "'{}':'{}',".format(name.replace(' county',''),vals[1])
        if n%5 == 0 and n > 0:
            outString += '\n'

    outString = outString.rstrip(',') + '}\n'

    opt = 'a' if refFile.exists() else 'w'
    with open(refFile,opt) as rf:
        for line in outString.split('\n'):
            rf.write(line + '\n')


def getFipsCode(geogLev,fipsNm,dictNm=None):
    if geogLev not in NEEDS_FIPS:
        return fipsNm
    elif geogLev == 'state':
        return fips.STATE[fipsNm.lower()]
    elif geogLev == 'county':
        return fips.COUNTY[dictNm.upper()][fipsNm.lower()]

def getFipsName(geogLev,fipsNum,state=None):
    invDict = {}
    
    if geogLev not in NEEDS_FIPS:
        return fipsNum
    elif geogLev == 'state':
        invDict ={num:name for name,num in fips.STATE.items()}
        return invDict[fipsNum.lower()]
    elif geogLev == 'county':
        invDict = {num:name for name,num in fips.COUNTY[state.upper()].items()}
        return invDict[fipsNum].capitalize()


def ConstructGeoClauses(geoDict,geoHeirarchy=None):
    '''Converts dictionary of geographies into a list of geographic query clause strings
    geogLev: the geography level for which the query is being made
    Values -> state, county, tract, block group
    geoDict: dictionary of names of geographic levels defining requested geography;
    Examples
    States -> {'state':[Washington,Florida]}
    Counties -> {'county':{Washington:[Snohomish,King,Pierce],Florida:[Brevard]}}
    Tracts -> {'tract':{Washington:{Snohomish:[Tract #'s],King:[Tract #'s],Pierce:[Tract #'s]},Florida:{Brevard:[Tract #'s]}}}'''
    GEOCODE = {'state':1,'county':2,r'tract':3,r'block%20group':4} if not geoHeirarchy else geoHeirarchy
    INVGEOCODE = {1:'state',2:'county',3:r'tract',4:r'block%20group'} if not geoHeirarchy else {y:x for x,y in geoHeirarchy.items()}
    geoClauseList = []

    def iterFunc(geostage,subStruct,curstage=0,state=None,subClause=None):
        curstage = geostage if curstage == 0 else curstage
        
        if curstage == 1:
            for item in subStruct:
                if item != r'*':
                    mainClause = f'{INVGEOCODE[geostage]}:{getFipsCode(INVGEOCODE[geostage],item,dictNm=state)}'
                else:
                    mainClause = fr'{geogLev}:*'

                fullClause = mainClause + subClause if subClause else mainClause
                geoClauseList.append(fullClause)
                
        else:
            curstage -= 1
            for geogNm,subStruct1 in subStruct.items():
                thisState = geogNm if geostage-curstage == 1 else state
                subClause = '' if (geostage - curstage == 1) else r'&'.join(subClause.split('&')[0:(geostage-curstage)])
                inClause = fr'&in={INVGEOCODE[geostage-curstage]}:{getFipsCode(INVGEOCODE[geostage-curstage],geogNm,dictNm=state)}'
                subClause = subClause + inClause if subClause else inClause
                
                iterFunc(geostage,subStruct1,curstage=curstage,state=thisState,subClause=subClause)


    for geogLev,subStruct in geoDict.items():
        geostage = GEOCODE[geogLev]
        iterFunc(geostage,subStruct)

    return geoClauseList


##Create a url to query the Census API
def ConstructURL(fields,geo,conditional=None,year=str(dtm.now().year-2)):
    queryURL = fr"https://api.census.gov/data/{year}/acs/acs5?get={','.join(fields)}&for={geo}"

    if conditional:
        queryURL = queryURL + fr"&{conditional}"
    
    return queryURL


##Build a pandas dataframe from the query results
def ConstructDF(queryURL,index=None):
    page = requests.get(queryURL)
    try:
        datasoup = bsp(page.content,'html.parser')
    except:
        raise Exception
    else:
        datalist = eval(datasoup.get_text().replace('\n',''))
        dataDict = dict(zip(datalist[0],[x for x in zip(*datalist[1:])]))
    
    datadf = pd.DataFrame(dataDict)
    if index:
        datadf.set_index(index,inplace=True)

    return datadf


##Combine pandas dataframes of query results into one dataframe
def CombineData(dfList,ax=0):
    combodf = pd.concat(dfList,axis=ax)

    return combodf


if '__name__' == '__main__':
    fields = 'NAME,B01003_001E'
    geo = r'state:*'
