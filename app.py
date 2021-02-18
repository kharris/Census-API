import flask, os, pandas as pd, pathlib, random, re, string, sqlite3
import getCensusData as gcd
from datetime import datetime as dtm
from pathlib import Path
from flask import Flask, g, render_template, request, jsonify, session


app = Flask(__name__)
app.secret_key = os.urandom(13)

DATABASE = r".\static\dataframes\data.db"

def get_db(act='open'):
    db = getattr(g,'_database',None)
    if db is None:
        db = g._database = sqlite3.connect(r".\static\dataframes\data.db")
        return db
    if act == 'close':
        db.close()
        #pathlib.Path(DATABASE).unlink()
        return

def formToLines(formObj):
    geodictList = []
    geoTypes = list(filter(lambda x: re.match(r'GeoType_[^0]',x),formObj.keys()))

    ##Loop through table geoTypes listed in geoSelectors above each table
    for key in geoTypes:
        tableNum = key.split('_')[1]
        geo = formObj[key]
        curStruct = gcd.geoHeirs[geo]
        numRows = len(list(filter(lambda x: re.match(fr'{curStruct[0]}_{tableNum}_[^0]',x),formObj.keys())))

        ##Loop through the rows in each table
        for r in range(1,numRows+1):
            ##If 'All' listed in last cell, replace with wildcard character
            if "all" not in formObj[fr'{curStruct[-1]}_{tableNum}_{r}'].lower().split(','):
                finalList = formObj[fr'{curStruct[-1]}_{tableNum}_{r}'].split(',')
            else:
                finalList = [r'*']

            ##If only one item in geoHeirarchy, create dictionary, else continue to loop
            if len(curStruct) == 1:
                geoHeirTemplate = {geo.lower().replace(' ','%20'):1}
                geodictList.append([{geo.lower():finalList},geoHeirTemplate])
            elif len(curStruct) == 2 and 'all' in formObj[fr'{curStruct[0]}_{tableNum}_{r}'].lower() and finalList == [r'*']:
                geoHeirTemplate = {geo.lower().replace(' ','%20'):1}
                geodictList.append([{geo.lower().replace(' ','%20'):finalList},geoHeirTemplate])
            else:
                geodict = finalList
                geoHeirTemplate = {curStruct[-1].lower().replace(' ','%20'):len(curStruct)}

                ##Loop through each cell in the row using the items in the geoHeirarchy list as a loop limit
                for n,lev in enumerate(curStruct[-2::-1],1):
                    ##If cell value == 'All' and lowest heirarchy is 'All' and the cell is not the top level of the geoHeirarchy, skip iteration
                    if formObj[fr'{lev}_{tableNum}_{r}'] == 'All' and finalList == [r'*'] and n < (len(curStruct)-1):
                        ##Lower the number for each preceeding entry in the geoHeirTemplate dictionary to account for the skipped step
                        for k,v in geoHeirTemplate.items():
                            geoHeirTemplate[k] = v-1
                        continue
                    else:
                        geoHeirTemplate.update({lev.lower().replace(' ','%20'):(len(curStruct) - n)})
                        geodict = {formObj[fr'{lev}_{tableNum}_{r}']:geodict}

                geodictList.append([{geo.lower():geodict},geoHeirTemplate])

    return geodictList


@app.route('/')
def home():
    return flask.render_template(r'input.html')

@app.route('/meow',methods=['POST'])
def print_meow():
    return request.form['meow']

@app.route('/results',methods=['GET','POST'])
def show_results():
    if request.method == 'POST':
        geoClauses = []
        #dataUrlList = []
        dfList = []
        yrDfList = []

        yearsList = []
        yearsInputParts = request.form['dataYears'].replace(' ','').split(',')
        for p in yearsInputParts:
            if '-' in p:
                yearsList.extend([str(n) for n in range(int(p.split('-')[0]),(int(p.split('-')[1])+1))])
            else:
                yearsList.append(p)
                

        fieldsList = [field.strip() for field in request.form['dataFields'].split(',')]

        geoLines = formToLines(request.form)
        
        for line in geoLines:
            geoClauses.extend(gcd.ConstructGeoClauses(line[0],geoHeirarchy=line[1]))

        for n,yr in enumerate(yearsList):
            for clause in geoClauses:
                dataUrl = gcd.ConstructURL(fieldsList,clause,year=yr)
                #dataUrlList.append(dataUrl)
                dfList.append(gcd.ConstructDF(dataUrl))
            yrDf = gcd.CombineData(dfList)
            dfList.clear()
            
            indList = [ind for ind in filter(lambda f: (f!='NAME') and ('_' not in f),yrDf.columns)]
            yrDf.set_index(indList,inplace=True)
            if n > 0:
                dropList = [drCol for drCol in filter(lambda f: '_' not in f,yrDf.columns)]
                yrDf.drop(dropList,axis=1,inplace=True)
            fieldSwitchDict = {oldf:f'{oldf}_{yr}' for oldf in yrDf.columns}
            yrDf.rename(fieldSwitchDict,axis=1,inplace=True)
            
            yrDfList.append(yrDf)
        
        bigDF = gcd.CombineData(yrDfList,ax=1)


        session['df_name'] = (''.join(random.choice(string.ascii_letters) for i in range(8)) + str(dtm.now().strftime(r'_%y%m%d_%H%M%S')))
        #bigDF.to_csv(fr"./static/dataframes/{session['df_name']}.csv")
        conn = get_db()
        bigDF.to_sql(session['df_name'],conn)

        return render_template('results.html',words=geoClauses,words2=yearsList,tables=[bigDF.to_html(classes='data')])
        #return render_template('results.html',words=geoClauses,words2=dataUrlList)

    else:
        return flask.redirect(flask.url_for('home'))

@app.route('/download_data',methods=['Post'])
def download_data():
        #df = pd.read_csv(fr"./static/dataframes/{session['df_name']}.csv")
        df = pd.read_sql(f"SELECT * from {session['df_name']};",get_db())
        df.to_excel(request.form['save-loc-input'])
        return "Saved!"

@app.route('/graphs')
def graphs():
    return "This is where you graph data!"

@app.route('/maps')
def maps():
    return "This is where your map shows up!"

@app.teardown_appcontext
def end_conn(exception):
    get_db(act='close')


if __name__ == '__main__':

    app.run()
