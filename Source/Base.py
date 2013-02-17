'''
Created on Feb 13, 2013

@author: ozbolt
'''

from datetime import datetime

class Movie(object):
    '''
    ### Data ###
    AttributeName    AttTyp
    *obligatory 
    
    *title           String
    originalTitle    String
    *director        String
    *actor           {int: String}[]
    *genre           {int: String}[]
    *plot            String //Long
    *runTime         int
    *year            int
    
    *language        {int: String}
    country          {int: String}
       
    *id_IMDB         int
    id_FB            int
    id_RT            int
    id_Netflix       int
    id_Amazon        int
    
    *IMDB_rating     double
    *IMDB_votes      int
    
    *released        boolean
    *dateRelease     Date
    
    releasedSQ       boolean
    releasedHD       boolean
    releases         Release[]
    
    releasedNetflix  boolean
    releaseNetflix   Release
    
    releasedAmazon   boolean
    releaseAmazon    Release
    
    linkTrailer      String
    *linkPhoto       String
    linkSite         String
    
    #Functions 
    
    '''
    
    def __init__(self, title = '', 
                 director = "", 
                 actor = {}, 
                 genre = {}, 
                 plot = "", 
                 runTime = -1, 
                 language = {},
                 id_IMDB = -1,
                 IMDB_rating = -1.0,
                 IMDB_votes = -1,
                 dateRelease = datetime(1970,1,1),
                 linkPhoto = "",
                 year = -1):
        '''
        Constructor creates obligatory attributes
        '''
        self.title = title
        self.director = director
        self.actor = actor
        self.genre = genre
        self.plot = plot
        self.runTime = runTime
        self.language = language
        self.id_IMDB = id_IMDB
        self.IMDB_rating = IMDB_rating
        self.IMDB_votes = IMDB_votes
        self.dateRelease = dateRelease
        self.linkPhoto = linkPhoto
        self.year = year
        self.releases = []
        
    def hasRelease(self, name):
        return False
        
    def constructDict(self, additional = False):
        variables = ["title", "director", "actor", "year", "genre", "plot", "runTime", "language", "id_IMDB", "IMDB_rating", "IMDB_votes", "dateRelease", "linkPhoto"]
        toRet = dict( (v, getattr(self, v)) for v in variables)
        return toRet
        
    def __str__(self):
        toRet = ""
        dct = self.constructDict()
        for k,v in dct.items():
            v = str(v)
            toRet += k +  " : " + v + "\n"
        return toRet
    
class Release:
    '''
    ### Data ###
    AttributeName    AttTyp 
    
    typ             int
    link            String
    releaseDate     Date
    data            {k:v}
       
    
    type:
        1 - SQ [500MB < rip < 1.5GB]
        2 - HD [1080p] [2.GB < rip < 10GB]
        3 - netflix
        4 - amazon
    
    data
        type{1,2}: 
         - size    int
         - seeds    int
         - peers    int
         - rls     String
         - hash    torrentzHash
        type{4}:
         - avaliable  1(Prime), 2(Rent), 3(Buy)
         - price      int

    #Functions 
    
    '''

    def __init__(self, typ, link = "", releaseDate = None, data = {}):
        self.typ = typ
        self.releaseDate = releaseDate
        self.data = data
        self.link = link
        
    def __str__(self):
        variables = ["typ", "link", "releaseDate"]
        dIct = dict( (v, getattr(self, v)) for v in variables)
        
        toRet = ""
        for k,v in dIct.items():
            v = str(v)
            toRet += k +  " : " + v + "\n"
        for k,v in self.data.items():
            toRet += "  " + k + " : " + str(v) + "\n"
            
        return toRet



if __name__ == "__main__":    
    r = Release(1, "mja", "vceraj", {"bla": None})
    print(r)
    
    