'''
Run with:

osascript -e 'tell app "Terminal" to do script "python ~/git/synXiv/synXiv.py"'



Cron job: 
# 7:20 on weekdays
20 7 * * 1-5 osascript -e 'tell app "Terminal" to do script "python ~/git/synXiv/synXiv.py"'
'''
from urllib import urlopen
from datetime import datetime

newURL = 'http://arxiv.org/list/astro-ph.EP/new?skip=0&show=1000'
new = urlopen(newURL).read().splitlines()
#with open('tmp.txt','w') as f:
#    f.write(tmp)
#with open('tmp.txt','r') as f:
#    new = f.read().splitlines()

# Where to put the data:
outputdir = '/Users/bmorris/Dropbox/synXiv/'

# Current date: 
currentyear = datetime.now().strftime('%Y')

# Don't include replacements: 
replacementsline = [i for i in range(len(new)) if 
                    new[i].startswith('<h3>Replacements')][0]
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
#savePDFs = [False, False, False]

def downloadPDF(PDFlinks, authorlist, savePDFs):
    for url, authors, save in zip(PDFlinks, authorlist, savePDFs):
        if save:
            firstauthor = authors[0]
            lastname = firstauthor.split(' ')[-1]
            raw = urlopen(url)
            outfilepath = outputdir+'{0}{1}.pdf'.format(lastname, currentyear)
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
    savePDFs.append(int(save))

downloadPDF(PDFlinks, authorlist, savePDFs)