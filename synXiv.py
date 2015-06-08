'''
synXiv: arXiv -> Terminal -> Dropbox

Run each morning to: 
1) See new papers (title/author/abstract) in your subfield
2) Choose if you'd like to download the PDF
3) Download PDFs to your Dropbox folder

then sync your tablet/phone's Dropbox folder and head out the door!

The script is intended to be run on Mac OS X with a cron job like this: 
    # 7:20am on weekdays
    20 7 * * 1-5 osascript -e 'tell app "Terminal" to do script "python /your/path/to/synXiv.py"'

You can run it from Terminal with:
    osascript -e 'tell app "Terminal" to do script "python /your/path/to/synXiv.py"'

'''
from urllib import urlopen
from datetime import datetime
import os

# Load input parameters from 'params.txt' file
paramspath = os.path.join(os.path.dirname(__file__),'params.txt')
with open(paramspath,'r') as f:
    params = f.read().splitlines()
    
# Which astro-ph sub-domain to read from:
subdomain = [line.split()[1] for line in params if line.startswith('subdomain')][0]
# Where to put the data:
outputdir = [line.split()[1] for line in params if line.startswith('outputdir')][0]
# How to format the date in the PDF output name
datestr = [line.split()[1] for line in params	 if line.startswith('datestr') ][0]

newURL = 'http://arxiv.org/list/{0}/new?skip=0&show=1000'.format(subdomain)
new = urlopen(newURL).read().splitlines()

# Current date: 
currentyear = datetime.now().strftime(datestr)

# Don't include replacements: 
startreplacements = '<h3>Replacements'
if startreplacements in ' '.join(new):
    replacementsline = [i for i in range(len(new)) if 
                        new[i].startswith(startreplacements)][0]
    new = new[:replacementsline]

# Get indices for references:
allindices = range(len(new))
closedivs = [i for i in allindices if new[i] == '</div>']
titlelines = [i for i in allindices if 
              new[i].startswith('<span class="descriptor">Title:</span>')]
openauthors = [i for i in allindices if 
               new[i].startswith('<div class="list-authors">')]
openabstracts = [i for i in allindices if new[i].startswith('<p>')]
closeabstracts = [i for i in allindices if new[i].startswith('</p>')]
PDFlines = [i for i in allindices if "Download PDF" in new[i]]

def nearestgreater(opendiv):
    s = sorted(closedivs + [opendiv])
    return closedivs[s.index(opendiv)+1]
    
closeauthors = map(nearestgreater, openauthors)

def getauthorlist(openauthors, closeauthors):
    allauthors = []
    for i, j in zip(openauthors, closeauthors):
        authorset = []
        authorlines = new[i:j]
        for line in authorlines:
            if line.startswith('<a href='):
                authorset.append(line.split('>')[1].split('<')[0])
        allauthors.append(authorset)
    return allauthors

def gettitles(titleline):
    return new[titleline].split('>')[2].split('<')[0]

def getabstracts(openabstracts, closeabstracts):
    abstracts = []
    for i, j in zip(openabstracts, closeabstracts):
        abstracts.append(' '.join(new[i:j])[3:])
    return abstracts

def getPDFlinks(PDFlines):
    PDFlinks = []
    for i in PDFlines:
        PDFlinks.append('http://arxiv.org/'+new[i].split('"')[9])
    return PDFlinks

authorlist = getauthorlist(openauthors, closeauthors)
titlelist = map(gettitles, titlelines)
abstracts = getabstracts(openabstracts, closeabstracts)
PDFlinks = getPDFlinks(PDFlines)

def downloadPDF(PDFlinks, authorlist, savePDFs):
    for url, authors, save in zip(PDFlinks, authorlist, savePDFs):
        if save:
            firstauthor = authors[0]
            lastname = firstauthor.split(' ')[-1]
            outfilepath = outputdir+'{0}{1}.pdf'.format(currentyear, lastname)
            raw = urlopen(url)
            print 'Saving: {0}'.format(outfilepath)
            with open(outfilepath, 'wb') as f:
                f.write(raw.read())

# Print options:
savePDFs = []
for title, authors, abstract in zip(titlelist, authorlist, abstracts):
    if title != titlelist[0]:
        print 30*'-'+'\n'
    print "\nTitle: {0}\n\nAuthor: {1}\n\nAbstract: {2}\n\n".format(
                title,
                ', '.join(authors),
                 abstract)
    save = raw_input('Pull to Dropbox? (0) No, (1) Yes: ')
    if save not in ['0', '1']: 
        save = '0'
    savePDFs.append(int(save))

downloadPDF(PDFlinks, authorlist, savePDFs)
