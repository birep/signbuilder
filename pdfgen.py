from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import flask_wkhtmltopdf
from flask_wkhtmltopdf import Wkhtmltopdf
from werkzeug.utils import secure_filename
import sys, os, csv, urllib, urllib2
import zipfile

UPLOAD_FOLDER = "C:/Python27/ArcGIS10.4/uploads/"
ALLOWED_EXTENSIONS = set(['csv'])

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['WKHTMLTOPDF_BIN_PATH'] = "C:\\Python27\\ArcGIS10.4\\Scripts\\wkhtmltopdf\\bin"
app.config['PDF_DIR_PATH'] = "C:\\Python27\\ArcGIS10.4\\static\\pdf"

wkhtmltopdf = Wkhtmltopdf(app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

script = """<script>$(document).ready( function() {
 $('#go').click(function() {
var signlist = {};
$('a').each( function(index) {
    if($(this).next('input').prop('checked')) {
    signlist[index] = $(this).attr('href') + "&color=red";
    }
    else {
    signlist[index] = $(this).attr('href') + "&color=green";
    }
    });
    $('div').fadeOut("slow").promise().done(function() {
        document.write("This will take a moment. You will be redirected shortly, please do not refresh.");
        $.post("/makezip", JSON.stringify(signlist), function( da ) {
        $('body').replaceWith(da);      
      });
        });
 });  

$('a').on('click', function(e)   {
    e.preventDefault();
    var theurl = $(this).attr('href');
    if($(this).next('input').prop('checked')) {
    window.open(theurl + "&color=red")
    }
    else {
    window.open(theurl + "&color=green")
    }
           });

});
</script>"""


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename)) as csvfile:
        reader = csv.DictReader(csvfile)
        output = []
        for row in reader:
            acnum = row['\xef\xbb\xbfAccNoFull']
            comname = row['CommonNameAll']
            taxname = row['TaxonName']
            origin = row['TaxonDistribution']
            fam = row['Family']
            output.append("<div><a href='/makesign?" + str(urllib.urlencode({'acnum':acnum, 'comname':comname, 'taxname':taxname, 'origin':origin,'fam':fam})) + "'>Sign for " + taxname + "</a> | Red sign? <input type='checkbox'></div>")
        output =  "<br>".join(list(set(output)))
        output = "<html><script src='" + url_for('static', filename='js/jquery.js') + "'></script><body>" + output + script
        return output + "<br><input id='go' type='button' value='Save all to Zip Archive'></body></html>"
    #return send_from_directory(app.config['UPLOAD_FOLDER'],
    #                           filename)

@app.route('/makesign')
def hello():
    acnum = request.args.get('acnum','')
    comname = request.args.get('comname','')
    taxname = request.args.get('taxname','')
    origin = request.args.get('origin','')
    fam = request.args.get('fam','')
    color = request.args.get('color','')
    return wkhtmltopdf.render_template_to_pdf("template.html", acnum=acnum, comname=comname, taxname=taxname, origin=origin, fam=fam,  color=color)

@app.route('/makezip',methods=['POST'])
def make_zip():
    zf = zipfile.ZipFile('c:/Python27/ArcGIS10.4/static/signorder.zip', mode="w")
    urldict = request.get_json(force=True)
    for i in range(len(urldict)):
        url = "http://localhost:5000" + urldict[str(i)] 
        print url
        response = urllib2.urlopen(url)
        trimmed = url[url.find("acnum=")+6:]
        acnum = trimmed[:trimmed.find("&")]
        zf.writestr(acnum + '.pdf', response.read())
    zf.close()
    return "<a href='" + url_for('static', filename='signorder.zip') + "'>Download Zip File</a>"

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
    return '''
    <!doctype html>
    <title>Upload IrisBG Label CSV</title>
    <h1>Upload new IrisBG label list</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    <br>
    <h2>Don't know how to create the CSV?</h2>
    <ol>
    <li>
    Connect to the Garden Jetpack with wifi password "InAValley"
    </li>
    <li>
    Open IrisBG. If prompted for user information the login is admin and the password is 666garden777</li>
    <li>If it's closed, open the "Events" tab group in the left column.</li>
    <li>
    Click on "Tasks" under the Events tab group.
    </li>
    <li>Under Task fill in some info, give the task a number name and start date.
    </li>
    <li>
    Change "Entry Kind" to "Taxon" and click the three little dots in the "Code/Name."</li>
    <li>
    Begin typing the plant you're looking for under the "Taxon Name" field; usually just a few letters will do. Click the binoculars to search for the accession record.
    </li>
    <li>&nbsp;When you've found the record, click "Select and Close"
    </li>
    <li>
    Add records for each sign you want created.
    </li>
    <li>&nbsp;Click "Save" in the Tasks tab (towards the top right)
    </li>
    <li>&nbsp;Switch to the "Item Management" tab under the "Collections" tab group.
    </li>
    <li>&nbsp;Under "Event Name" select the list you just created.
    </li>
    <li>&nbsp;Switch from the "Update Items" tab to the "Create Labels" tab.
    </li>
    <li>&nbsp;For label type choose "SIGN"
    </li>
    <li>&nbsp;Press the Binocular button to add the items from your list.
    </li>
    <li>&nbsp;Press "Export."
    </li>
    <li>&nbsp;Choose Save as type "CSV" and save the file somewhere.</li>
    <li>Press "Check/Uncheck All" so these signs are not accidentally included in your next order.</li>
</ol>

    '''
if __name__ == '__main__':
    app.run(threaded=True)