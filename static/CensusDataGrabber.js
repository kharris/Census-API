function setTable(el){
    const geog_options = {"State" : ["State"], "County" : ["State","County"], "Tract" : ["State","County","Tract"],
                        "Block%20Group" : ["State","County","Tract","Block Group"], "Congressional%20District" :
                        ["State","Congressional District"]};

    var rowNum = 0;
    var tableNum = el.dataset.tableId;
    var geoType = document.querySelector("select[name=GeoType_"+tableNum+"]").value;
    var header = document.querySelector("div.justTable[data-table-id=\""+tableNum+"\"] thead tr");
    var headerLen = header.childElementCount;
    var bodyRows = [].slice.call(document.querySelectorAll("div.justTable[data-table-id=\""+tableNum+"\"] tbody tr"));
    var buttonDiv = document.querySelector("div.justButtons[data-table-id=\""+tableNum+"\"]");
    var rowControls = [].slice.call(buttonDiv.querySelectorAll("button"));
    var numButtons = rowControls.length - 1;

    //Add the header row to the array of rows from the table body and loop through all rows
    bodyRows.unshift(header);
    bodyRows.forEach(function(rowThing){
        //Loop through all cells in a row
        for(var i=0;i<geog_options[geoType].length;i++){
            //Repurpose existing cells where possible
            if(i < headerLen){
                if(rowThing.className == "head"){
                    var child = rowThing.querySelectorAll("td")[i];

                    child.innerText = geog_options[geoType][i];
                }
                else{
                    var child = rowThing.querySelectorAll("td")[i];
                    var childInput = child.querySelector("input");

                    child.className = geog_options[geoType][i];
                    child.name = geog_options[geoType][i]+"_"+String(tableNum)+"_"+rowNum;
                    childInput.className = geog_options[geoType][i];
                    childInput.name = geog_options[geoType][i]+"_"+String(tableNum)+"_"+rowNum;
                }
            }
            //Create new cells in the row when moving from a shorter geoheirarchy to a longer one
            else{
                var child = document.createElement("td");

                if(rowThing.className == "head"){                    
                    child.innerText = geog_options[geoType][i];
                    rowThing.append(child);
                }
                else{
                    var childInput = document.createElement("input");

                    childInput.className = geog_options[geoType][i];
                    childInput.setAttribute("data-table-id",tableNum);
                    childInput.setAttribute("data-row-id",rowNum);
                    childInput.name = geog_options[geoType][i]+"_"+childInput.dataset.tableId+"_"+childInput.dataset.rowId;
                    childInput.value = "All";

                    child.append(childInput);
                    rowThing.append(child);
                }
            }
        }
        //Remove extra cells in a row when moving from a longer geoheirarchy to a shorter one
        if(geog_options[geoType].length < headerLen){
            for(var i=(headerLen-1);i>=geog_options[geoType].length;i--){
                console.log("dropping: ",rowThing.querySelectorAll("td")[i]);
                rowThing.querySelectorAll("td")[i].remove();
            }
        }
        //Advance to the next row in the table and repeat the for loop
        rowNum++;
    });

    //Loop through row control buttons below table
    for(var i=0;i<geog_options[geoType].length;i++){
        //Repurpose existing buttons where possible
        if(i < headerLen){
            rowControls[i].innerText = "Add "+geog_options[geoType][i];
        }
        //Add buttons when moving from a shorter geoheirarchy to a longer one
        else{
            var newButton = document.createElement("button")

            newButton.type = "button";
            newButton.setAttribute("data-table-id",tableNum);
            newButton.setAttribute("data-button-id",i);
            newButton.addEventListener("click",function(){addRow(this);},false);
            newButton.innerText = "Add "+geog_options[geoType][i];

            buttonDiv.insertBefore(newButton,buttonDiv.querySelector("br"));
        }
    }
    //Remove extra buttons when moving from a longer geoheirarchy to an shorter one
    if(geog_options[geoType].length < headerLen){
        for(var i=(headerLen-1);i>=geog_options[geoType].length;i--){
            rowControls[i].remove();
        }
    }
}

function addRow(el){
    var tableBod = document.querySelector("tbody[name=body_"+el.dataset.tableId+"]");
    var tblRows = tableBod.querySelectorAll("tr");
    var newRow = tblRows[tblRows.length-1].cloneNode(true);
    var cells = newRow.getElementsByTagName("td");

    newRow.dataset.tableId = tableBod.getAttribute('name').split("_")[1];
    newRow.dataset.rowId = tblRows.length+1;
    for(var i=0;i<cells.length;i++){
        var curCell = cells[i].getElementsByTagName("input")[0];
        if(i>=el.dataset.buttonId){
            curCell.value = "All";
        }
        
        curCell.dataset.rowId = newRow.dataset.rowId;
        curCell.name = curCell.name.split('_')[0] + '_' + curCell.dataset.tableId + "_" + curCell.dataset.rowId;
    }
    
    tableBod.appendChild(newRow);
}

function dropRow(el){
    var tableBod = document.querySelector("tbody[name=body_"+el.dataset.tableId+"]");
    var lastRow = tableBod.lastChild;

    lastRow.remove();

}

function dropTable(el){
    var tableEl = document.querySelector("div.geoTableForm[data-table-id=\""+el.dataset.tableId+"\"]");
    tableEl.remove();
}

function addTable(el){
    if(el.id=="copy-table"){
        var prevTable = parseInt(el.dataset.tableId); 
    }
    else{
        var prevTable = 0;
    }

    var prevGeoTableEl = document.querySelector("div.geoTableForm[data-table-id=\""+prevTable+"\"]");
    var tableArr = document.querySelectorAll("table");
    var newGeoTableEl = prevGeoTableEl.cloneNode(true);
    var newGeoSelect = newGeoTableEl.querySelector("select");
    
    if(prevTable == 0){var thisTable = tableArr.length;}
    else{var thisTable = prevTable+1;}

    newGeoTableEl.dataset.tableId = thisTable;
    newGeoTableEl.setAttribute("name","geoTableForm_"+newGeoTableEl.dataset.tableId);

   var tableIdEls = [].slice.call(newGeoTableEl.querySelectorAll("[data-table-id]"));
   tableIdEls.forEach(function(elem){
       elem.setAttribute("data-table-id",thisTable);
       if(elem.hasAttribute("name")){var nameParts = elem.getAttribute("name").split("_");
            if(elem.hasAttribute("data-row-id")){elem.setAttribute("name",(nameParts[0]+"_"+thisTable+"_"+nameParts[2]));}
            else{elem.setAttribute("name",(nameParts[0]+"_"+thisTable));}
       }
   });

    if(prevTable==0 || prevTable == (tableArr.length-1)){
        prevGeoTableEl.parentElement.append(newGeoTableEl);
    }
    else{
        prevGeoTableEl.parentElement.after(newGeoTableEl,prevGeoTableEl);
    }

    newGeoTableEl.querySelector("select").value = prevGeoTableEl.querySelector("select").value;
    newGeoTableEl.hidden = false;
}

function createDownload(){
    var downldButton = document.querySelector("button#download-data-button");
    var buttonParent = downldButton.parentElement;
    var wrapperForm = document.createElement("form");
    var inputField = document.createElement("input");
    var inputLabel = document.createElement("label");

    //Replace the "Download your data" button with a form to get output filepath
    buttonParent.replaceChild(wrapperForm,downldButton);
    wrapperForm.name="save-to";
    wrapperForm.method="post";
    wrapperForm.action="download_data";
    wrapperForm.target="_blank";

    //Add the file path input button within the new form
    wrapperForm.append(inputField);
    inputField.type="text";
    inputField.name="save-loc-input";
    inputField.required=true;

    //Add the label for the filepath input above the filepath input button
    wrapperForm.insertBefore(inputLabel,inputField);
    inputLabel.target="save-loc-input";
    inputLabel.innerText="Output Location: ";

    //Add a linebreak between the filepath input and the download button
    wrapperForm.append(document.createElement('br'));

    //Add the download button below the filepath input
    wrapperForm.append(downldButton);
    downldButton.removeAttribute('onclick');
    downldButton.type="submit";
    downldButton.innerText="Download";

    //Add linebreaks to seperate the form from the table below
    buttonParent.insertBefore(document.createElement('br'),wrapperForm.nextSibling);
}