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
    
    releasedDVDrip   boolean
    releasesDVDrip   Release[]
    
    releasedBRrip    boolean
    releasesBRrip    Release[]
    
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
    imdbID          int
    link            String
    releaseDate     Date
    data            {k:v}
       
    
    type:
        1 - DVDrip
        2 - BDrip
        3 - netflix
        4 - amazon
    
    data1
        type{1,2}: 
         - size    int
         - seed    int
         - leechs  int
         - rls     String
         - hash    torrentzHash
        type{4}:
         - avaliable  1(Prime), 2(Rent), 3(Buy)
         - price      int

    #Functions 
    
    '''

    def __init__(self, typ, id_IMDB, link, released, data):
        self.typ = typ
        self.imdbI = id_IMDB
        self.released = released
        self.data = data    
    



if __name__ == "__main__":    
    a = Movie(title = 'La vita e bella',
              director = "Roberto Benigni")
    
    print(a)